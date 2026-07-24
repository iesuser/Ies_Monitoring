from flask_restx import fields, inputs, reqparse

from app.extensions import api

accounts_ns = api.namespace(
    "Accounts",
    description="Accounts and profile endpoints",
    path="/accounts",
)

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

account_update_parser = reqparse.RequestParser()
account_update_parser.add_argument("first_name", type=str, required=False)
account_update_parser.add_argument("last_name", type=str, required=False)
account_update_parser.add_argument("email", type=inputs.email(check=True), required=False)
account_update_parser.add_argument("is_active", type=inputs.boolean, required=False)

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

error_model = accounts_ns.model(
    "ErrorResponse",
    {
        "error": fields.String(required=True, example="forbidden"),
        "message": fields.String(required=True, example="Missing required permission: can_permissions"),
    },
)
