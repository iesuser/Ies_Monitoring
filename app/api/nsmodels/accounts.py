from flask_restx import fields, inputs, reqparse

from app.extensions import api

accounts_ns = api.namespace(
    "Accounts",
    description="Accounts and profile endpoints",
    path="/accounts",
)

JWT_OR_API_KEY = ["JsonWebToken", "ApiKeyAuth"]

account_model = accounts_ns.model(
    "Account",
    {
        "uuid": fields.String(required=True, example="0f6fd0fa-cceb-4f25-a79b-c9f8f3444bc2"),
        "email": fields.String(required=True, example="user@example.com"),
        "first_name": fields.String(required=True, example="Nino"),
        "last_name": fields.String(required=True, example="Beridze"),
        "is_active": fields.Boolean(required=True, example=True),
        "created_at": fields.String(required=False, example="2026-07-24T11:22:33"),
        "updated_at": fields.String(required=False, example="2026-07-24T11:22:33"),
    },
)

current_user_model = accounts_ns.inherit(
    "CurrentAccount",
    account_model,
    {
        "can_users": fields.Boolean(
            required=False,
            example=True,
        ),
        "can_permissions": fields.Boolean(
            required=False,
            example=True,
        ),
        "can_recips": fields.Boolean(
            required=False,
            example=True,
        ),
        "can_event_view": fields.Boolean(
            required=False,
            example=True,
        ),
        "can_event_edit": fields.Boolean(
            required=False,
            example=True,
        ),
    },
)

permission_model = accounts_ns.model(
    "Permission",
    {
        "id": fields.Integer(required=True, example=1),
        "code": fields.String(required=True, example="can_recips"),
        "name": fields.String(required=True, example="Recips Management"),
        "description": fields.String(required=False, example="Manage notification recipients."),
        "is_active": fields.Boolean(required=True, example=True),
    },
)

user_permission_model = accounts_ns.model(
    "UserPermission",
    {
        "id": fields.Integer(required=True, example=1),
        "permission_id": fields.Integer(required=True, example=1),
        "code": fields.String(required=True, example="can_recips"),
        "name": fields.String(required=True, example="Recips Management"),
        "description": fields.String(required=False),
        "granted_at": fields.String(required=False, example="2026-08-04T12:00:00"),
        "granted_by_user_id": fields.Integer(required=False, example=1),
    },
)

permission_list_response_model = accounts_ns.model(
    "PermissionListResponse",
    {
        "items": fields.List(fields.Nested(permission_model), required=True),
        "total": fields.Integer(required=True, example=4),
    },
)

user_permission_list_response_model = accounts_ns.model(
    "UserPermissionListResponse",
    {
        "items": fields.List(fields.Nested(user_permission_model), required=True),
        "total": fields.Integer(required=True, example=1),
        "user_uuid": fields.String(required=True),
    },
)

account_update_parser = reqparse.RequestParser()
account_update_parser.add_argument("first_name", type=str, required=False)
account_update_parser.add_argument("last_name", type=str, required=False)
account_update_parser.add_argument("email", type=inputs.email(check=True), required=False)
account_update_parser.add_argument("is_active", type=inputs.boolean, required=False)

grant_permissions_parser = reqparse.RequestParser()
grant_permissions_parser.add_argument(
    "permission_codes",
    type=str,
    required=False,
    action="append",
    help="Permission codes to grant, e.g. can_recips",
)
grant_permissions_parser.add_argument(
    "permission_ids",
    type=int,
    required=False,
    action="append",
    help="Permission ids to grant",
)

account_update_response_model = accounts_ns.model(
    "AccountUpdateResponse",
    {
        "message": fields.String(required=True, example="User updated successfully."),
        "user": fields.Nested(account_model, required=True),
    },
)

account_list_response_model = accounts_ns.model(
    "AccountListResponse",
    {
        "items": fields.List(fields.Nested(account_model), required=True),
        "total": fields.Integer(required=True, example=1),
    },
)

account_delete_response_model = accounts_ns.model(
    "AccountDeleteResponse",
    {
        "message": fields.String(required=True, example="User deleted successfully."),
    },
)

permission_action_response_model = accounts_ns.model(
    "PermissionActionResponse",
    {
        "message": fields.String(required=True, example="Permissions updated successfully."),
        "granted": fields.List(fields.String, required=False),
        "revoked": fields.List(fields.String, required=False),
        "permissions": fields.List(fields.Nested(user_permission_model), required=False),
    },
)

error_model = accounts_ns.model(
    "ErrorResponse",
    {
        "error": fields.String(required=True, example="forbidden"),
        "message": fields.String(required=True, example="Missing required permission: can_users"),
    },
)
