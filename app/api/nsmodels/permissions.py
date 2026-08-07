from flask_restx import fields, reqparse

from app.extensions import api

permissions_ns = api.namespace(
    "Permissions",
    description="Permission catalog management (list, create, delete)",
    path="/permissions",
)

JWT_OR_API_KEY = ["JsonWebToken", "ApiKeyAuth"]

permission_model = permissions_ns.model(
    "PermissionCatalogItem",
    {
        "id": fields.Integer(required=True, example=1),
        "code": fields.String(required=True, example="can_recips"),
        "name": fields.String(required=True, example="Recips Management"),
        "description": fields.String(required=False, example="Manage notification recipients."),
        "is_active": fields.Boolean(required=True, example=True),
        "created_at": fields.String(required=False, example="2026-08-04T12:00:00"),
        "updated_at": fields.String(required=False, example="2026-08-04T12:00:00"),
    },
)

permission_list_response_model = permissions_ns.model(
    "PermissionCatalogListResponse",
    {
        "items": fields.List(fields.Nested(permission_model), required=True),
        "total": fields.Integer(required=True, example=4),
    },
)

permission_create_parser = reqparse.RequestParser()
permission_create_parser.add_argument(
    "code",
    type=str,
    required=True,
    help="Unique permission code, e.g. can_event_view",
)
permission_create_parser.add_argument(
    "name",
    type=str,
    required=True,
    help="Human-readable name",
)
permission_create_parser.add_argument(
    "description",
    type=str,
    required=False,
    help="Optional description",
)

permission_create_response_model = permissions_ns.model(
    "PermissionCreateResponse",
    {
        "message": fields.String(required=True, example="Permission created successfully."),
        "permission": fields.Nested(permission_model, required=True),
    },
)

permission_delete_response_model = permissions_ns.model(
    "PermissionDeleteResponse",
    {
        "message": fields.String(required=True, example="Permission deleted successfully."),
    },
)

error_model = permissions_ns.model(
    "PermissionErrorResponse",
    {
        "error": fields.String(required=True, example="forbidden"),
        "message": fields.String(
            required=True,
            example="Missing required permission: can_permissions",
        ),
    },
)
