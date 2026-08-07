from datetime import datetime

from flask_restx import fields, inputs, reqparse

from app.extensions import api

seismic_events_ns = api.namespace(
    "Seismic Events",
    description="Seismic events, magnitudes, and beachball management endpoints",
    path="/seismic_events",
)

JWT_OR_API_KEY = ["JsonWebToken", "ApiKeyAuth"]


def parse_datetime(value):
    """Parse ISO-like datetime strings for request parsers."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError as err:
        raise ValueError(
            "Invalid datetime format. Use ISO 8601, e.g. 2026-08-05T12:30:00"
        ) from err


magnitude_catalog_model = seismic_events_ns.model(
    "MagnitudeCatalogItem",
    {
        "id": fields.Integer(required=True, example=1),
        "code": fields.String(required=True, example="MW"),
        "description": fields.String(
            required=False,
            example="Moment Magnitude – Calculated from the seismic moment.",
        ),
    },
)

event_magnitude_model = seismic_events_ns.model(
    "EventMagnitude",
    {
        "id": fields.Integer(required=True, example=1),
        "event_id": fields.Integer(required=True, example=1),
        "magnitude_id": fields.Integer(required=True, example=5),
        "value": fields.Float(required=True, example=4.2),
        "magnitude": fields.Nested(magnitude_catalog_model, required=False),
    },
)

event_beachball_model = seismic_events_ns.model(
    "EventBeachball",
    {
        "id": fields.Integer(required=True, example=1),
        "event_id": fields.Integer(required=True, example=1),
        "rake": fields.Float(required=False, example=90.0),
        "dip": fields.Float(required=False, example=45.0),
        "strike": fields.Float(required=False, example=180.0),
        "beachball_path": fields.String(
            required=False,
            example="/static/beachballs/event_1.png",
        ),
    },
)

seismic_event_model = seismic_events_ns.model(
    "SeismicEvent",
    {
        "id": fields.Integer(required=True, example=1),
        "iesdata_id": fields.String(required=False, example="IES-2026-0001"),
        "seiscomp_oid": fields.String(required=False, example="Origin/20260805.123456.01"),
        "origin_time": fields.String(required=True, example="2026-08-05T12:30:00"),
        "latitude": fields.Float(required=True, example=41.7151),
        "longitude": fields.Float(required=True, example=44.8271),
        "depth": fields.Float(required=False, example=10.5),
        "location_ge": fields.String(required=False, example="თბილისის მახლობლად"),
        "location_en": fields.String(required=False, example="Near Tbilisi"),
        "area": fields.String(required=False, example="Georgia"),
        "is_automatic": fields.Boolean(required=True, example=False),
        "created_at": fields.String(required=False, example="2026-08-05T12:31:00"),
        "magnitudes": fields.List(fields.Nested(event_magnitude_model), required=True),
        "beachball": fields.Nested(event_beachball_model, required=False, allow_null=True),
    },
)

seismic_event_list_response_model = seismic_events_ns.model(
    "SeismicEventListResponse",
    {
        "items": fields.List(fields.Nested(seismic_event_model), required=True),
        "total": fields.Integer(required=True, example=1),
    },
)

seismic_event_response_model = seismic_events_ns.model(
    "SeismicEventResponse",
    {
        "message": fields.String(required=True, example="Seismic event created successfully."),
        "event": fields.Nested(seismic_event_model, required=True),
    },
)

event_magnitude_response_model = seismic_events_ns.model(
    "EventMagnitudeResponse",
    {
        "message": fields.String(required=True, example="Event magnitude added successfully."),
        "event_magnitude": fields.Nested(event_magnitude_model, required=True),
    },
)

event_beachball_response_model = seismic_events_ns.model(
    "EventBeachballResponse",
    {
        "message": fields.String(required=True, example="Beachball saved successfully."),
        "beachball": fields.Nested(event_beachball_model, required=True),
    },
)

magnitude_catalog_list_response_model = seismic_events_ns.model(
    "MagnitudeCatalogListResponse",
    {
        "items": fields.List(fields.Nested(magnitude_catalog_model), required=True),
        "total": fields.Integer(required=True, example=11),
    },
)

message_response_model = seismic_events_ns.model(
    "SeismicEventMessageResponse",
    {
        "message": fields.String(required=True, example="Seismic event deleted successfully."),
    },
)

error_model = seismic_events_ns.model(
    "SeismicEventErrorResponse",
    {
        "error": fields.String(required=True, example="forbidden"),
        "message": fields.String(
            required=True,
            example="Missing required permission: can_event_edit",
        ),
    },
)

seismic_event_create_parser = reqparse.RequestParser()
seismic_event_create_parser.add_argument(
    "origin_time",
    type=parse_datetime,
    required=True,
    help="Origin time ISO 8601, e.g. 2026-08-05T12:30:00",
)
seismic_event_create_parser.add_argument("latitude", type=float, required=True, help="Latitude")
seismic_event_create_parser.add_argument("longitude", type=float, required=True, help="Longitude")
seismic_event_create_parser.add_argument("depth", type=float, required=False, help="Depth in km")
seismic_event_create_parser.add_argument("iesdata_id", type=str, required=False, help="External IES data id")
seismic_event_create_parser.add_argument(
    "seiscomp_oid",
    type=str,
    required=False,
    help="SeisComP object id",
)
seismic_event_create_parser.add_argument("location_ge", type=str, required=False, help="Location in Georgian")
seismic_event_create_parser.add_argument("location_en", type=str, required=False, help="Location in English")
seismic_event_create_parser.add_argument("area", type=str, required=False, help="Area / region")
seismic_event_create_parser.add_argument(
    "is_automatic",
    type=inputs.boolean,
    required=False,
    default=False,
    help="Whether the event was created automatically (default: false)",
)

seismic_event_update_parser = reqparse.RequestParser()
seismic_event_update_parser.add_argument(
    "origin_time",
    type=parse_datetime,
    required=False,
    help="Origin time ISO 8601, e.g. 2026-08-05T12:30:00",
)
seismic_event_update_parser.add_argument("latitude", type=float, required=False, help="Latitude")
seismic_event_update_parser.add_argument("longitude", type=float, required=False, help="Longitude")
seismic_event_update_parser.add_argument("depth", type=float, required=False, help="Depth in km")
seismic_event_update_parser.add_argument("iesdata_id", type=str, required=False, help="External IES data id")
seismic_event_update_parser.add_argument(
    "seiscomp_oid",
    type=str,
    required=False,
    help="SeisComP object id",
)
seismic_event_update_parser.add_argument("location_ge", type=str, required=False, help="Location in Georgian")
seismic_event_update_parser.add_argument("location_en", type=str, required=False, help="Location in English")
seismic_event_update_parser.add_argument("area", type=str, required=False, help="Area / region")
seismic_event_update_parser.add_argument(
    "is_automatic",
    type=inputs.boolean,
    required=False,
    help="Whether the event was created automatically",
)

event_magnitude_create_parser = reqparse.RequestParser()
event_magnitude_create_parser.add_argument(
    "value",
    type=float,
    required=True,
    help="Magnitude value, e.g. 4.2",
)
event_magnitude_create_parser.add_argument(
    "magnitude_id",
    type=int,
    required=False,
    help="Magnitude catalog id (alternative to magnitude_code)",
)
event_magnitude_create_parser.add_argument(
    "magnitude_code",
    type=str,
    required=False,
    help="Magnitude catalog code, e.g. MW / ML",
)

event_magnitude_update_parser = reqparse.RequestParser()
event_magnitude_update_parser.add_argument(
    "value",
    type=float,
    required=False,
    help="Magnitude value, e.g. 4.2",
)
event_magnitude_update_parser.add_argument(
    "magnitude_id",
    type=int,
    required=False,
    help="Magnitude catalog id (alternative to magnitude_code)",
)
event_magnitude_update_parser.add_argument(
    "magnitude_code",
    type=str,
    required=False,
    help="Magnitude catalog code, e.g. MW / ML",
)

event_beachball_parser = reqparse.RequestParser()
event_beachball_parser.add_argument("rake", type=float, required=False, help="Rake angle")
event_beachball_parser.add_argument("dip", type=float, required=False, help="Dip angle")
event_beachball_parser.add_argument("strike", type=float, required=False, help="Strike angle")
event_beachball_parser.add_argument(
    "beachball_path",
    type=str,
    required=False,
    help="Path or URL to beachball image",
)

seismic_event_filter_parser = reqparse.RequestParser()
seismic_event_filter_parser.add_argument(
    "event_id",
    type=int,
    required=False,
    help="Exact seismic event id",
)
seismic_event_filter_parser.add_argument(
    "iesdata_id",
    type=str,
    required=False,
    help="Substring match against IES data id",
)
seismic_event_filter_parser.add_argument(
    "seiscomp_oid",
    type=str,
    required=False,
    help="Substring match against SeisComP object id",
)
seismic_event_filter_parser.add_argument(
    "location",
    type=str,
    required=False,
    help="Substring match against location_en or location_ge",
)
seismic_event_filter_parser.add_argument(
    "area",
    type=str,
    required=False,
    help="Substring match against area",
)
seismic_event_filter_parser.add_argument(
    "magnitude",
    type=str,
    required=False,
    help="Magnitude catalog code, e.g. MW / ML (filters by that type)",
)
seismic_event_filter_parser.add_argument(
    "magnitude_min",
    type=float,
    required=False,
    help="Minimum magnitude value (inclusive)",
)
seismic_event_filter_parser.add_argument(
    "magnitude_max",
    type=float,
    required=False,
    help="Maximum magnitude value (inclusive)",
)
seismic_event_filter_parser.add_argument(
    "depth_min",
    type=float,
    required=False,
    help="Minimum depth in km (inclusive)",
)
seismic_event_filter_parser.add_argument(
    "depth_max",
    type=float,
    required=False,
    help="Maximum depth in km (inclusive)",
)
seismic_event_filter_parser.add_argument(
    "date_from",
    type=parse_datetime,
    required=False,
    help="Origin time from (ISO 8601, inclusive)",
)
seismic_event_filter_parser.add_argument(
    "date_to",
    type=parse_datetime,
    required=False,
    help="Origin time to (ISO 8601, inclusive)",
)
