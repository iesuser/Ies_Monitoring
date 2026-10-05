from flask_restx import fields

from app.extensions import api

alert_zones_ns = api.namespace(
    "AlertZones",
    description="Alert zone (map polygon) management endpoints",
    path="/api",
)

JWT_OR_API_KEY = ["JsonWebToken", "ApiKeyAuth"]

_POLYGON_EXAMPLE = [[
    [44.70, 41.65],
    [44.90, 41.65],
    [44.90, 41.80],
    [44.70, 41.80],
    [44.70, 41.65],
]]

alert_zone_geometry_model = alert_zones_ns.model(
    "AlertZoneGeometry",
    {
        "type": fields.String(required=True, example="Polygon"),
        "coordinates": fields.Raw(
            required=True,
            example=_POLYGON_EXAMPLE,
            description="GeoJSON Polygon rings: [[[lon, lat], ...]]",
        ),
    },
)

alert_zone_model = alert_zones_ns.model(
    "AlertZone",
    {
        "id": fields.Integer(required=True, example=1),
        "name": fields.String(required=True, example="Tbilisi"),
        "geometry": fields.Nested(alert_zone_geometry_model, required=True),
        "min_magnitude": fields.Float(required=True, example=4.0, description="ML magnitude threshold lower bound"),
        "max_magnitude": fields.Float(
            required=False,
            example=7.0,
            description="ML magnitude threshold upper bound; null means no upper limit",
        ),
        "enabled": fields.Boolean(required=True, example=True),
        "notif_is_staff": fields.Boolean(required=True, example=True),
        "notif_channels": fields.List(fields.String, required=True, example=["mail", "push_notif"]),
        "created_at": fields.String(required=False, example="2026-10-05T12:00:00"),
        "updated_at": fields.String(required=False, example="2026-10-05T12:00:00"),
        "created_by_user_id": fields.Integer(required=False, example=1),
        "updated_by_user_id": fields.Integer(required=False, example=1),
    },
)

alert_zone_create_model = alert_zones_ns.model(
    "AlertZoneCreate",
    {
        "name": fields.String(required=True, example="Tbilisi"),
        "geometry": fields.Nested(alert_zone_geometry_model, required=True),
        "min_magnitude": fields.Float(required=True, example=4.0, description="ML magnitude threshold lower bound"),
        "max_magnitude": fields.Float(required=False, example=7.0, description="ML magnitude threshold upper bound"),
        "enabled": fields.Boolean(required=False, default=True, example=True),
        "notif_is_staff": fields.Boolean(required=False, default=False, example=True),
        "notif_channels": fields.List(
            fields.String,
            required=True,
            example=["mail", "push_notif"],
            description="Any of: mail, number, push_notif",
        ),
    },
)

alert_zone_update_model = alert_zones_ns.model(
    "AlertZoneUpdate",
    {
        "name": fields.String(required=False, example="Tbilisi"),
        "geometry": fields.Nested(alert_zone_geometry_model, required=False),
        "min_magnitude": fields.Float(required=False, example=4.5, description="ML magnitude threshold lower bound"),
        "max_magnitude": fields.Float(
            required=False,
            example=7.0,
            description="ML magnitude threshold upper bound; send null to remove the upper limit",
        ),
        "enabled": fields.Boolean(required=False, example=False),
        "notif_is_staff": fields.Boolean(required=False, example=False),
        "notif_channels": fields.List(
            fields.String,
            required=False,
            example=["number"],
            description="Any of: mail, number, push_notif",
        ),
    },
)

alert_zone_response_model = alert_zones_ns.model(
    "AlertZoneResponse",
    {
        "message": fields.String(required=True, example="Alert zone created successfully."),
        "alert_zone": fields.Nested(alert_zone_model, required=True),
    },
)

alert_zone_list_response_model = alert_zones_ns.model(
    "AlertZoneListResponse",
    {
        "items": fields.List(fields.Nested(alert_zone_model), required=True),
        "total": fields.Integer(required=True, example=1),
    },
)

message_response_model = alert_zones_ns.model(
    "AlertZoneMessageResponse",
    {
        "message": fields.String(required=True, example="Alert zone deleted successfully."),
    },
)

error_model = alert_zones_ns.model(
    "AlertZoneErrorResponse",
    {
        "error": fields.String(required=True, example="validation_error"),
        "message": fields.String(required=True, example='geometry.type must be "Polygon".'),
    },
)
