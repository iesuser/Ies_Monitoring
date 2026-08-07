import logging
from datetime import datetime

from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restx import Resource, marshal
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.api.nsmodels import (
    accounts_ns,
    account_model,
    current_user_model,
    account_update_parser,
    account_update_response_model,
    account_list_response_model,
    account_delete_response_model,
    grant_permissions_parser,
    user_permission_list_response_model,
    permission_action_response_model,
    error_model,
)
from app.api.nsmodels.accounts import JWT_OR_API_KEY
from app.models import User, Permission, UserPermission, RefreshToken
from app.utils.auth_utils import require_permissions, resolve_actor
from app.utils.validators import normalize_email

logger = logging.getLogger("app.accounts")


def _require_can_users():
    return require_permissions("can_users")


def _require_manage_permissions():
    """Grant/revoke user permissions requires can_permissions only."""
    return require_permissions("can_permissions")


def _normalize_codes(raw_values):
    if raw_values is None:
        return []
    if isinstance(raw_values, str):
        values = [raw_values]
    elif isinstance(raw_values, (list, tuple)):
        values = list(raw_values)
    else:
        values = [str(raw_values)]

    codes = []
    for item in values:
        if item is None:
            continue
        nested = item if isinstance(item, (list, tuple)) else str(item).split(",")
        for code in nested:
            normalized = str(code).strip()
            if normalized and normalized not in codes:
                codes.append(normalized)
    return codes


def _normalize_ids(raw_values):
    if raw_values is None:
        return []
    if isinstance(raw_values, int):
        return [raw_values]
    if isinstance(raw_values, (list, tuple)):
        ids = []
        for item in raw_values:
            try:
                value = int(item)
            except (TypeError, ValueError):
                continue
            if value not in ids:
                ids.append(value)
        return ids
    try:
        return [int(raw_values)]
    except (TypeError, ValueError):
        return []


def _active_user_permission_rows(user):
    return (
        db.session.query(UserPermission, Permission)
        .join(Permission, Permission.id == UserPermission.permission_id)
        .filter(
            UserPermission.user_id == user.id,
            UserPermission.degranted_at.is_(None),
            Permission.is_active.is_(True),
        )
        .order_by(Permission.code.asc())
        .all()
    )


def _user_permission_payload(user):
    items = []
    for assignment, permission in _active_user_permission_rows(user):
        items.append(
            {
                "id": assignment.id,
                "permission_id": permission.id,
                "code": permission.code,
                "name": permission.name,
                "description": permission.description,
                "granted_at": assignment.granted_at.isoformat() if assignment.granted_at else None,
                "granted_by_user_id": assignment.granted_by_user_id,
            }
        )
    return items


def _user_delete_blockers(user):
    """Return human-readable reasons why a hard delete is not allowed."""
    blockers = []

    created_users = User.query.filter(
        User.created_by_user_id == user.id,
        User.id != user.id,
    ).count()
    if created_users:
        blockers.append(f"{created_users} user(s) created by this account")

    updated_users = User.query.filter(
        User.updated_by_user_id == user.id,
        User.id != user.id,
    ).count()
    if updated_users:
        blockers.append(f"{updated_users} user(s) last updated by this account")

    permission_refs = Permission.query.filter(
        or_(
            Permission.created_by_user_id == user.id,
            Permission.updated_by_user_id == user.id,
            Permission.deactivated_by_user_id == user.id,
        )
    ).count()
    if permission_refs:
        blockers.append(f"{permission_refs} permission record(s) reference this account")

    permission_grant_refs = UserPermission.query.filter(
        or_(
            UserPermission.granted_by_user_id == user.id,
            UserPermission.degranted_by_user_id == user.id,
        ),
        UserPermission.user_id != user.id,
    ).count()
    if permission_grant_refs:
        blockers.append(
            f"{permission_grant_refs} permission assignment(s) reference this account as grantor"
        )

    return blockers


@accounts_ns.route("/ourself")
class CurrentUserApi(Resource):
    @jwt_required()
    @accounts_ns.doc(security="JsonWebToken")
    @accounts_ns.marshal_with(current_user_model, code=200)
    @accounts_ns.response(404, "Not Found", error_model)
    def get(self):
        """Get current authenticated user."""
        identity = get_jwt_identity()
        user = User.query.filter_by(uuid=identity, is_active=True).first()
        if not user:
            return {"error": "not_found", "message": "User not found."}, 404
        user_data = user.to_dict()
        user_data["can_users"] = user.check_permission("can_users")
        user_data["can_permissions"] = user.check_permission("can_permissions")
        user_data["can_recips"] = user.check_permission("can_recips")
        user_data["can_event_view"] = user.check_permission("can_event_view")
        user_data["can_event_edit"] = user.check_permission("can_event_edit")
        return user_data

    @jwt_required()
    @accounts_ns.doc(security="JsonWebToken")
    @accounts_ns.expect(account_update_parser)
    @accounts_ns.marshal_with(account_update_response_model, code=200)
    @accounts_ns.response(400, "Validation Error", error_model)
    @accounts_ns.response(404, "Not Found", error_model)
    def put(self):
        """Update current authenticated user profile."""
        identity = get_jwt_identity()
        user = User.query.filter_by(uuid=identity, is_active=True).first()
        if not user:
            return {"error": "not_found", "message": "User not found."}, 404

        payload = account_update_parser.parse_args()
        first_name = payload.get("first_name")
        last_name = payload.get("last_name")

        if first_name is not None:
            value = first_name.strip()
            if not value:
                return {"error": "validation_error", "message": "first_name cannot be empty."}, 400
            user.first_name = value
        if last_name is not None:
            value = last_name.strip()
            if not value:
                return {"error": "validation_error", "message": "last_name cannot be empty."}, 400
            user.last_name = value

        user.updated_by_user_id = user.id
        user.save()
        return {"message": "Profile updated successfully.", "user": user.to_dict()}, 200


@accounts_ns.route("/")
class AccountsApi(Resource):
    @accounts_ns.doc(security=JWT_OR_API_KEY)
    @accounts_ns.response(200, "Success", account_list_response_model)
    @accounts_ns.response(401, "Unauthorized", error_model)
    @accounts_ns.response(403, "Forbidden", error_model)
    def get(self):
        """List all users (JWT or API key with can_users)."""
        denied = _require_can_users()
        if denied:
            return denied

        users = User.query.order_by(User.id.asc()).all()
        return marshal(
            {"items": [u.to_dict() for u in users], "total": len(users)},
            account_list_response_model,
        ), 200


@accounts_ns.route("/<string:user_uuid>/permissions")
class AccountPermissionsApi(Resource):
    @accounts_ns.doc(security=JWT_OR_API_KEY)
    @accounts_ns.response(200, "Success", user_permission_list_response_model)
    @accounts_ns.response(401, "Unauthorized", error_model)
    @accounts_ns.response(403, "Forbidden", error_model)
    @accounts_ns.response(404, "Not Found", error_model)
    def get(self, user_uuid):
        """List active permissions for a user."""
        denied = _require_manage_permissions()
        if denied:
            return denied

        user = User.query.filter_by(uuid=user_uuid).first()
        if not user:
            return {"error": "not_found", "message": "User not found."}, 404

        items = _user_permission_payload(user)
        return (
            marshal(
                {"items": items, "total": len(items), "user_uuid": user.uuid},
                user_permission_list_response_model,
            ),
            200,
        )

    @accounts_ns.doc(parser=grant_permissions_parser, security=JWT_OR_API_KEY)
    @accounts_ns.response(200, "Success", permission_action_response_model)
    @accounts_ns.response(400, "Validation Error", error_model)
    @accounts_ns.response(401, "Unauthorized", error_model)
    @accounts_ns.response(403, "Forbidden", error_model)
    @accounts_ns.response(404, "Not Found", error_model)
    @accounts_ns.response(409, "Conflict", error_model)
    def post(self, user_uuid):
        """Grant one or more permissions to a user (by code and/or id)."""
        denied = _require_manage_permissions()
        if denied:
            return denied

        actor = resolve_actor()
        user = User.query.filter_by(uuid=user_uuid).first()
        if not user:
            return {"error": "not_found", "message": "User not found."}, 404

        args = grant_permissions_parser.parse_args()
        json_body = request.get_json(silent=True) or {}

        codes = _normalize_codes(args.get("permission_codes") or json_body.get("permission_codes"))
        ids = _normalize_ids(args.get("permission_ids") or json_body.get("permission_ids"))
        # Accept simpler body: {"permissions": ["can_recips", ...]}
        if not codes and not ids:
            codes = _normalize_codes(json_body.get("permissions"))

        if not codes and not ids:
            return {
                "error": "validation_error",
                "message": "Provide permission_codes and/or permission_ids.",
            }, 400

        permissions_by_id = {}
        for permission_id in ids:
            permission = Permission.query.filter_by(id=permission_id).first()
            if not permission:
                return {
                    "error": "validation_error",
                    "message": f"Unknown permission id(s): {permission_id}",
                }, 400
            permissions_by_id[permission.id] = permission

        for code in codes:
            permission = Permission.query.filter_by(code=code).first()
            if not permission:
                return {
                    "error": "validation_error",
                    "message": f"Unknown permission code(s): {code}",
                }, 400
            permissions_by_id[permission.id] = permission

        granted = []
        already = []
        inactive = []
        for permission in permissions_by_id.values():
            if not permission.is_active:
                inactive.append(permission.code)
                continue

            active = UserPermission.query.filter_by(
                user_id=user.id,
                permission_id=permission.id,
                degranted_at=None,
            ).first()
            if active:
                already.append(permission.code)
                continue

            assignment = UserPermission(
                user_id=user.id,
                permission_id=permission.id,
                granted_by_user_id=actor["user_id"],
            )
            assignment.create(commit=False)
            granted.append(permission.code)

        if inactive and not granted and not already:
            return {
                "error": "validation_error",
                "message": f"Inactive permission code(s): {', '.join(inactive)}",
            }, 400

        if already and not granted:
            return {
                "error": "already_assigned",
                "message": f"Permission already assigned: {', '.join(already)}",
            }, 409

        UserPermission.save()
        logger.info(
            "Permissions granted: actor=%s target_uuid=%s granted=%s already=%s",
            actor["label"],
            user.uuid,
            granted,
            already,
        )
        return (
            marshal(
                {
                    "message": "Permissions granted successfully.",
                    "granted": granted,
                    "permissions": _user_permission_payload(user),
                },
                permission_action_response_model,
            ),
            200,
        )


@accounts_ns.route("/<string:user_uuid>/permissions/<string:permission_code>")
class AccountPermissionDetailApi(Resource):
    @accounts_ns.doc(security=JWT_OR_API_KEY)
    @accounts_ns.response(200, "Success", permission_action_response_model)
    @accounts_ns.response(401, "Unauthorized", error_model)
    @accounts_ns.response(403, "Forbidden", error_model)
    @accounts_ns.response(404, "Not Found", error_model)
    def delete(self, user_uuid, permission_code):
        """Revoke an active permission from a user (soft degrant)."""
        denied = _require_manage_permissions()
        if denied:
            return denied

        actor = resolve_actor()
        user = User.query.filter_by(uuid=user_uuid).first()
        if not user:
            return {"error": "not_found", "message": "User not found."}, 404

        permission = Permission.query.filter_by(code=permission_code).first()
        if not permission:
            return {"error": "not_found", "message": "Permission not found."}, 404

        assignment = UserPermission.query.filter_by(
            user_id=user.id,
            permission_id=permission.id,
            degranted_at=None,
        ).first()
        if not assignment:
            return {
                "error": "not_assigned",
                "message": f"Permission is not assigned: {permission_code}",
            }, 404

        # Protect last admin from removing own can_users if it would lock everyone out —
        # only block self-revoke of can_users / can_permissions for own account.
        if actor["user"] and actor["user"].id == user.id and permission_code in {
            "can_users",
            "can_permissions",
        }:
            return {
                "error": "conflict",
                "message": f"You cannot revoke your own {permission_code} permission.",
            }, 409

        assignment.degranted_at = datetime.now()
        assignment.degranted_by_user_id = actor["user_id"]
        db.session.commit()

        logger.info(
            "Permission revoked: actor=%s target_uuid=%s code=%s",
            actor["label"],
            user.uuid,
            permission_code,
        )
        return (
            marshal(
                {
                    "message": "Permission revoked successfully.",
                    "revoked": [permission_code],
                    "permissions": _user_permission_payload(user),
                },
                permission_action_response_model,
            ),
            200,
        )


@accounts_ns.route("/<string:user_uuid>")
class AccountDetailApi(Resource):
    @accounts_ns.doc(security=JWT_OR_API_KEY)
    @accounts_ns.response(200, "Success", account_model)
    @accounts_ns.response(401, "Unauthorized", error_model)
    @accounts_ns.response(403, "Forbidden", error_model)
    @accounts_ns.response(404, "Not Found", error_model)
    def get(self, user_uuid):
        """Get a single user by UUID (JWT or API key with can_users)."""
        denied = _require_can_users()
        if denied:
            return denied

        user = User.query.filter_by(uuid=user_uuid).first()
        if not user:
            return {"error": "not_found", "message": "User not found."}, 404

        payload = user.to_dict()
        payload["permissions"] = [item["code"] for item in _user_permission_payload(user)]
        return payload, 200

    @accounts_ns.doc(security=JWT_OR_API_KEY)
    @accounts_ns.expect(account_update_parser)
    @accounts_ns.response(200, "Success", account_update_response_model)
    @accounts_ns.response(400, "Validation Error", error_model)
    @accounts_ns.response(401, "Unauthorized", error_model)
    @accounts_ns.response(403, "Forbidden", error_model)
    @accounts_ns.response(404, "Not Found", error_model)
    @accounts_ns.response(409, "Conflict", error_model)
    def put(self, user_uuid):
        """Update a user by UUID (JWT or API key with can_users)."""
        denied = _require_can_users()
        if denied:
            return denied

        actor = resolve_actor()
        user = User.query.filter_by(uuid=user_uuid).first()
        if not user:
            return {"error": "not_found", "message": "User not found."}, 404

        payload = account_update_parser.parse_args()

        if payload.get("first_name") is not None:
            value = (payload.get("first_name") or "").strip()
            if not value:
                return {"error": "validation_error", "message": "first_name cannot be empty."}, 400
            user.first_name = value

        if payload.get("last_name") is not None:
            value = (payload.get("last_name") or "").strip()
            if not value:
                return {"error": "validation_error", "message": "last_name cannot be empty."}, 400
            user.last_name = value

        if payload.get("email") is not None:
            try:
                normalized_email = normalize_email(payload.get("email"))
            except ValueError as err:
                return {"error": "validation_error", "message": str(err)}, 400

            existing = User.query.filter_by(email=normalized_email).first()
            if existing and existing.id != user.id:
                return {"error": "conflict", "message": "Email address is already registered."}, 409
            user.email = normalized_email

        if payload.get("is_active") is not None:
            new_is_active = bool(payload.get("is_active"))
            if actor["user"] and user.id == actor["user"].id and not new_is_active:
                return {
                    "error": "conflict",
                    "message": "You cannot deactivate your own account.",
                }, 409
            user.is_active = new_is_active

        user.updated_by_user_id = actor["user_id"]
        db.session.commit()
        logger.info("Account updated: actor=%s target_uuid=%s", actor["label"], user.uuid)
        return marshal(
            {"message": "User updated successfully.", "user": user.to_dict()},
            account_update_response_model,
        ), 200

    @accounts_ns.doc(security=JWT_OR_API_KEY)
    @accounts_ns.response(200, "Success", account_delete_response_model)
    @accounts_ns.response(401, "Unauthorized", error_model)
    @accounts_ns.response(403, "Forbidden", error_model)
    @accounts_ns.response(404, "Not Found", error_model)
    @accounts_ns.response(409, "Conflict", error_model)
    def delete(self, user_uuid):
        """Delete a user by UUID when related records allow it (JWT or API key with can_users)."""
        denied = _require_can_users()
        if denied:
            return denied

        actor = resolve_actor()
        user = User.query.filter_by(uuid=user_uuid).first()
        if not user:
            return {"error": "not_found", "message": "User not found."}, 404

        if actor["user"] and user.id == actor["user"].id:
            return {"error": "conflict", "message": "You cannot delete your own account."}, 409

        blockers = _user_delete_blockers(user)
        if blockers:
            return {
                "error": "conflict",
                "message": "User cannot be deleted because related records still reference this account: "
                + "; ".join(blockers),
            }, 409

        try:
            RefreshToken.query.filter_by(user_id=user.id).delete(synchronize_session=False)
            UserPermission.query.filter_by(user_id=user.id).delete(synchronize_session=False)

            if user.created_by_user_id == user.id:
                user.created_by_user_id = None
            if user.updated_by_user_id == user.id:
                user.updated_by_user_id = None

            user.delete()
        except IntegrityError:
            logger.warning(
                "Account delete blocked by integrity constraint: actor=%s target_uuid=%s",
                actor["label"],
                user_uuid,
            )
            return {
                "error": "conflict",
                "message": "User cannot be deleted because related database records still reference this account.",
            }, 409

        logger.info("Account deleted: actor=%s target_uuid=%s", actor["label"], user_uuid)
        return marshal({"message": "User deleted successfully."}, account_delete_response_model), 200
