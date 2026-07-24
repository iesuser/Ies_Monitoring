import logging

from flask_jwt_extended import current_user, get_jwt_identity, jwt_required
from flask_restx import Resource

from app.extensions import db
from app.api.nsmodels import (
    accounts_ns,
    account_model,
    account_update_parser,
    account_update_response_model,
    account_list_response_model,
    error_model,
)
from app.models import User
from app.utils.validators import normalize_email

logger = logging.getLogger("app.accounts")


def _permission_denied():
    return {"error": "forbidden", "message": "Missing required permission: can_permissions"}, 403


@accounts_ns.route("/user")
class CurrentUserApi(Resource):
    @jwt_required()
    @accounts_ns.doc(security="JsonWebToken")
    @accounts_ns.marshal_with(account_model, code=200)
    @accounts_ns.response(404, "Not Found", error_model)
    def get(self):
        """Get current authenticated user."""
        identity = get_jwt_identity()
        user = User.query.filter_by(uuid=identity, is_active=True).first()
        if not user:
            return {"error": "not_found", "message": "User not found."}, 404
        return user.to_dict()

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


@accounts_ns.route("/accounts")
class AccountsApi(Resource):
    @jwt_required()
    @accounts_ns.doc(security="JsonWebToken")
    @accounts_ns.marshal_with(account_list_response_model, code=200)
    @accounts_ns.response(403, "Forbidden", error_model)
    def get(self):
        """List all users (requires can_permissions)."""
        if not current_user.check_permission("can_permissions"):
            return _permission_denied()

        users = User.query.order_by(User.id.asc()).all()
        return {"items": [u.to_dict() for u in users], "total": len(users)}, 200


@accounts_ns.route("/accounts/<string:user_uuid>")
class AccountDetailApi(Resource):
    @jwt_required()
    @accounts_ns.doc(security="JsonWebToken")
    @accounts_ns.marshal_with(account_model, code=200)
    @accounts_ns.response(403, "Forbidden", error_model)
    @accounts_ns.response(404, "Not Found", error_model)
    def get(self, user_uuid):
        """Get a single user by UUID (requires can_permissions)."""
        if not current_user.check_permission("can_permissions"):
            return _permission_denied()

        user = User.query.filter_by(uuid=user_uuid).first()
        if not user:
            return {"error": "not_found", "message": "User not found."}, 404
        return user.to_dict()

    @jwt_required()
    @accounts_ns.doc(security="JsonWebToken")
    @accounts_ns.expect(account_update_parser)
    @accounts_ns.marshal_with(account_update_response_model, code=200)
    @accounts_ns.response(400, "Validation Error", error_model)
    @accounts_ns.response(403, "Forbidden", error_model)
    @accounts_ns.response(404, "Not Found", error_model)
    @accounts_ns.response(409, "Conflict", error_model)
    def put(self, user_uuid):
        """Update a user by UUID (requires can_permissions)."""
        if not current_user.check_permission("can_permissions"):
            return _permission_denied()

        user = User.query.filter_by(uuid=user_uuid).first()
        if not user:
            return {"error": "not_found", "message": "User not found."}, 404

        payload = account_update_parser.parse_args()

        if "first_name" in payload:
            value = (payload.get("first_name") or "").strip()
            if not value:
                return {"error": "validation_error", "message": "first_name cannot be empty."}, 400
            user.first_name = value

        if "last_name" in payload:
            value = (payload.get("last_name") or "").strip()
            if not value:
                return {"error": "validation_error", "message": "last_name cannot be empty."}, 400
            user.last_name = value

        if "email" in payload:
            try:
                normalized_email = normalize_email(payload.get("email"))
            except ValueError as err:
                return {"error": "validation_error", "message": str(err)}, 400

            existing = User.query.filter_by(email=normalized_email).first()
            if existing and existing.id != user.id:
                return {"error": "conflict", "message": "Email address is already registered."}, 409
            user.email = normalized_email

        if "is_active" in payload:
            user.is_active = bool(payload.get("is_active"))

        user.updated_by_user_id = current_user.id
        db.session.commit()
        logger.info("Account updated: actor_uuid=%s target_uuid=%s", current_user.uuid, user.uuid)
        return {"message": "User updated successfully.", "user": user.to_dict()}, 200