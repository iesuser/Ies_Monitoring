import logging

from flask import Response, request
from flask_restx import Resource, marshal
from sqlalchemy import String, and_, case, cast, exists, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.api.nsmodels.seismic_events import (
    seismic_events_ns,
    JWT_OR_API_KEY,
    seismic_event_model,
    seismic_event_list_response_model,
    seismic_event_response_model,
    event_magnitude_model,
    event_magnitude_response_model,
    event_beachball_model,
    event_beachball_response_model,
    magnitude_catalog_list_response_model,
    message_response_model,
    error_model,
    seismic_event_create_parser,
    seismic_event_update_parser,
    seismic_event_get_parser,
    seismic_event_filter_parser,
    event_magnitude_create_parser,
    event_magnitude_update_parser,
    event_beachball_parser,
    parse_number,
)
from app.models import SeismicEvent, Magnitude, EventMagnitude, EventBeachball, PublishedEvent
from app.utils.auth_utils import require_permissions, resolve_actor
from app.utils.gen_beachball_img import delete_beachball_image, sync_beachball_image
from app.utils.shakemap_client import (
    ShakeMapError,
    delete_event as delete_shakemap_event,
    fetch_product,
    load_view,
    sync_event,
)

logger = logging.getLogger("app.seismic_events")

LIST_DEFAULT_LIMIT = 100
LIST_MAX_LIMIT = 200


def _event_load_options():
    """Load magnitudes, beachball, and publish row in the same query as the event."""
    return (
        selectinload(SeismicEvent.event_magnitudes).selectinload(EventMagnitude.magnitude),
        selectinload(SeismicEvent.beachball),
        selectinload(SeismicEvent.published_event),
        selectinload(SeismicEvent.created_by_user),
        selectinload(SeismicEvent.updated_by_user),
        selectinload(SeismicEvent.created_by_service),
        selectinload(SeismicEvent.updated_by_service),
    )


def _lookup_event(event_id, seiscomp_oid, iesdata_id):
    """Exact match on the given keys. Uses the unique indexes and reads one row."""
    query = SeismicEvent.query.options(*_event_load_options())
    if event_id is not None:
        query = query.filter(SeismicEvent.id == event_id)
    if seiscomp_oid is not None:
        query = query.filter(SeismicEvent.seiscomp_oid == seiscomp_oid)
    if iesdata_id is not None:
        query = query.filter(SeismicEvent.iesdata_id == iesdata_id)
    return query.limit(1).first()


def _require_can_event_view():
    return require_permissions("can_event_edit", "can_event_view", "can_event_publish")


def _require_can_event_edit():
    return require_permissions("can_event_edit")


def _apply_generated_beachball_path(beachball):
    """Generate PNG when strike/dip/rake are complete; store web path on the model."""
    web_path = sync_beachball_image(
        beachball.event_id,
        beachball.strike,
        beachball.dip,
        beachball.rake,
    )
    if web_path is not None:
        beachball.beachball_path = web_path
    return web_path


def _validate_beachball_mechanism_payload(payload):
    """
    Require all of strike, dip, rake together, or none of them.

    Returns None if valid, or (error_body, status_code).
    """
    provided = [
        name
        for name in ("strike", "dip", "rake")
        if payload.get(name) is not None
    ]
    if len(provided) in (0, 3):
        return None
    return {
        "error": "validation_error",
        "message": (
            "strike, dip, and rake must all be provided together "
            "(or omit all three)."
        ),
        "provided": provided,
    }, 400


def _get_event_or_404(event_id):
    event = _lookup_event(event_id, None, None)
    if not event:
        return None, ({"error": "not_found", "message": "Seismic event not found."}, 404)
    return event, None


def _event_detail_or_404(event):
    if event is None:
        return {"error": "not_found", "message": "Seismic event not found."}, 404
    return marshal(event.to_dict(), seismic_event_model), 200


def _maybe_sync_shakemap(event):
    """Send a saved event to ShakeMap when it has a SeisComP id, depth, and ML.

    A ShakeMap failure is logged and does not undo the event stored here.
    """
    try:
        sync_event(event)
    except Exception:
        logger.exception(
            "ShakeMap sync failed: event_id=%s seiscomp_oid=%s",
            event.id,
            event.seiscomp_oid,
        )


def _maybe_delete_shakemap(seiscomp_oid):
    """Remove the matching ShakeMap event. Local delete is not undone on failure."""
    if not (seiscomp_oid or "").strip():
        return
    try:
        delete_shakemap_event(seiscomp_oid)
    except Exception:
        logger.exception(
            "ShakeMap delete failed: seiscomp_oid=%s",
            seiscomp_oid,
        )


def _optional_str(value):
    if value is None:
        return None
    text = str(value).strip()
    return text or None


# K (energy class) is a logarithm of energy, not a magnitude scale; typical values are 5-17.
MAGNITUDE_VALUE_RANGES = {"K": (0, 20)}
DEFAULT_MAGNITUDE_VALUE_RANGE = (-2, 10)


def _magnitude_value_error(magnitude, value):
    code = (magnitude.code or "").upper()
    minimum, maximum = MAGNITUDE_VALUE_RANGES.get(code, DEFAULT_MAGNITUDE_VALUE_RANGE)
    if minimum <= value <= maximum:
        return None
    return {
        "error": "validation_error",
        "message": f"{code} value must be a number between {minimum:g} and {maximum:g}.",
    }, 400


def _resolve_magnitude(magnitude_id=None, magnitude_code=None):
    if magnitude_id is not None:
        magnitude = Magnitude.query.filter_by(id=magnitude_id).first()
        if not magnitude:
            return None, ({"error": "not_found", "message": "Magnitude catalog entry not found."}, 404)
        return magnitude, None

    if magnitude_code is not None:
        code = str(magnitude_code).strip().upper()
        if not code:
            return None, (
                {"error": "validation_error", "message": "magnitude_code cannot be empty."},
                400,
            )
        magnitude = Magnitude.query.filter_by(code=code).first()
        if not magnitude:
            return None, (
                {
                    "error": "not_found",
                    "message": f"Magnitude catalog entry not found for code: {code}",
                },
                404,
            )
        return magnitude, None

    return None, (
        {
            "error": "validation_error",
            "message": "Provide magnitude_id or magnitude_code.",
        },
        400,
    )


REQUIRED_EVENT_FIELDS = ("origin_time", "latitude", "longitude")
OPTIONAL_TEXT_FIELDS = ("seiscomp_oid", "location_ge", "location_en", "area")


def _apply_event_fields(event, payload, *, creating=False):
    """
    Copy parsed fields onto the event.

    Create sets every field. Update (payload holds only the keys the client sent)
    changes the sent keys; null clears an optional field and is rejected for required ones.
    """
    for field in REQUIRED_EVENT_FIELDS:
        if creating or field in payload:
            if payload.get(field) is None:
                return {"error": "validation_error", "message": f"{field} is required."}, 400
            setattr(event, field, payload[field])

    for field in ("depth", "iesdata_id"):
        if creating or field in payload:
            setattr(event, field, payload.get(field))

    for field in OPTIONAL_TEXT_FIELDS:
        if creating or field in payload:
            value = _optional_str(payload.get(field))
            max_length = SeismicEvent.__table__.c[field].type.length
            if value is not None and max_length and len(value) > max_length:
                return {
                    "error": "validation_error",
                    "message": f"{field} must be at most {max_length} characters.",
                }, 400
            setattr(event, field, value)

    if creating:
        event.is_automatic = bool(payload.get("is_automatic") or False)
    elif payload.get("is_automatic") is not None:
        event.is_automatic = bool(payload["is_automatic"])
    else:
        # A manual edit means the event was reviewed. Ingestion services send
        # is_automatic explicitly, so their updates keep the value they choose.
        event.is_automatic = False

    return None


def _normalize_magnitude_criteria(payload):
    """Build magnitude filter criteria from `magnitudes` list or legacy single fields."""
    raw_list = payload.get("magnitudes")
    if isinstance(raw_list, list) and raw_list:
        criteria = []
        for item in raw_list:
            if not isinstance(item, dict):
                return None, (
                    {
                        "error": "validation_error",
                        "message": "Each magnitudes entry must be an object.",
                    },
                    400,
                )
            try:
                magnitude_min = parse_number(item.get("magnitude_min", item.get("min")))
                magnitude_max = parse_number(item.get("magnitude_max", item.get("max")))
            except ValueError:
                return None, (
                    {
                        "error": "validation_error",
                        "message": "magnitude_min and magnitude_max must be numbers.",
                    },
                    400,
                )
            criteria.append(
                {
                    "code": _optional_str(
                        item.get("magnitude") or item.get("magnitude_code") or item.get("code")
                    ),
                    "min": magnitude_min,
                    "max": magnitude_max,
                }
            )
        return criteria, None

    code = _optional_str(payload.get("magnitude"))
    magnitude_min = payload.get("magnitude_min")
    magnitude_max = payload.get("magnitude_max")
    if code is None and magnitude_min is None and magnitude_max is None:
        return [], None
    return [{"code": code, "min": magnitude_min, "max": magnitude_max}], None


def _apply_magnitude_criteria(query, criteria):
    """AND together magnitude constraints using EXISTS subqueries."""
    for criterion in criteria:
        code = criterion.get("code")
        magnitude_min = criterion.get("min")
        magnitude_max = criterion.get("max")

        if (
            magnitude_min is not None
            and magnitude_max is not None
            and magnitude_min > magnitude_max
        ):
            return None, (
                {
                    "error": "validation_error",
                    "message": "magnitude_min cannot be greater than magnitude_max.",
                },
                400,
            )

        conditions = [EventMagnitude.event_id == SeismicEvent.id]
        if code is not None:
            magnitude = Magnitude.query.filter_by(code=code.upper()).first()
            if not magnitude:
                return None, (
                    {
                        "error": "not_found",
                        "message": f"Magnitude catalog entry not found for code: {code.upper()}",
                    },
                    404,
                )
            conditions.append(EventMagnitude.magnitude_id == magnitude.id)
        if magnitude_min is not None:
            conditions.append(EventMagnitude.value >= magnitude_min)
        if magnitude_max is not None:
            conditions.append(EventMagnitude.value <= magnitude_max)

        query = query.filter(exists().where(and_(*conditions)))

    return query, None


def _build_filtered_events_query(payload):
    """Build a SeismicEvent query from optional filter args. Returns (query, error_tuple)."""
    event_id = payload.get("event_id")
    event_query = _optional_str(payload.get("event_query"))
    iesdata_id = payload.get("iesdata_id")
    seiscomp_oid = _optional_str(payload.get("seiscomp_oid"))
    location = _optional_str(payload.get("location"))
    area = _optional_str(payload.get("area"))
    depth_min = payload.get("depth_min")
    depth_max = payload.get("depth_max")
    date_from = payload.get("date_from")
    date_to = payload.get("date_to")

    magnitude_criteria, magnitude_error = _normalize_magnitude_criteria(payload)
    if magnitude_error:
        return None, magnitude_error

    if depth_min is not None and depth_max is not None and depth_min > depth_max:
        return None, (
            {
                "error": "validation_error",
                "message": "depth_min cannot be greater than depth_max.",
            },
            400,
        )
    if date_from is not None and date_to is not None and date_from > date_to:
        return None, (
            {
                "error": "validation_error",
                "message": "date_from cannot be after date_to.",
            },
            400,
        )

    query = SeismicEvent.query

    if event_id is not None:
        query = query.filter(SeismicEvent.id == event_id)

    if event_query is not None:
        pattern = f"%{event_query}%"
        query = query.filter(
            or_(
                cast(SeismicEvent.id, String).ilike(pattern),
                cast(SeismicEvent.iesdata_id, String).ilike(pattern),
            )
        )

    if iesdata_id is not None:
        query = query.filter(SeismicEvent.iesdata_id == iesdata_id)

    if seiscomp_oid is not None:
        query = query.filter(SeismicEvent.seiscomp_oid.ilike(f"%{seiscomp_oid}%"))

    if location is not None:
        pattern = f"%{location}%"
        query = query.filter(
            or_(
                SeismicEvent.location_en.ilike(pattern),
                SeismicEvent.location_ge.ilike(pattern),
            )
        )

    if area is not None:
        query = query.filter(SeismicEvent.area.ilike(f"%{area}%"))

    if depth_min is not None:
        query = query.filter(SeismicEvent.depth >= depth_min)
    if depth_max is not None:
        query = query.filter(SeismicEvent.depth <= depth_max)

    if date_from is not None:
        query = query.filter(SeismicEvent.origin_time >= date_from)
    if date_to is not None:
        query = query.filter(SeismicEvent.origin_time <= date_to)

    if magnitude_criteria:
        query, magnitude_apply_error = _apply_magnitude_criteria(query, magnitude_criteria)
        if magnitude_apply_error:
            return None, magnitude_apply_error

    return query, None


def _validated_limit(limit):
    """Returns (limit, error_tuple)."""
    if limit is None:
        return LIST_DEFAULT_LIMIT, None
    if limit < 1 or limit > LIST_MAX_LIMIT:
        return None, (
            {
                "error": "validation_error",
                "message": f"limit must be between 1 and {LIST_MAX_LIMIT}.",
            },
            400,
        )
    return limit, None


def _validated_page(args):
    """Returns (limit, offset, error_tuple)."""
    limit, error = _validated_limit(args.get("limit"))
    if error:
        return None, None, error
    offset = args.get("offset")
    if offset is None:
        return limit, 0, None
    if offset < 0:
        return None, None, (
            {"error": "validation_error", "message": "offset cannot be negative."},
            400,
        )
    return limit, offset, None


def _preferred_magnitude_expr():
    """ML value if the event has one, else its first recorded magnitude (same rule as the UI)."""
    ml_value = (
        select(EventMagnitude.value)
        .join(Magnitude, Magnitude.id == EventMagnitude.magnitude_id)
        .where(EventMagnitude.event_id == SeismicEvent.id, func.upper(Magnitude.code) == "ML")
        .order_by(EventMagnitude.id)
        .limit(1)
        .scalar_subquery()
    )
    first_value = (
        select(EventMagnitude.value)
        .where(EventMagnitude.event_id == SeismicEvent.id)
        .order_by(EventMagnitude.id)
        .limit(1)
        .scalar_subquery()
    )
    return func.coalesce(ml_value, first_value)


def _sort_expr(sort):
    if sort == "magnitude":
        return _preferred_magnitude_expr()
    if sort == "depth":
        return SeismicEvent.depth
    if sort == "type":
        return SeismicEvent.is_automatic
    if sort == "published":
        is_published = exists().where(PublishedEvent.event_id == SeismicEvent.id)
        return case((is_published, 1), else_=0)
    return SeismicEvent.origin_time


def _events_page(query, limit, offset=0, sort=None, order=None):
    """Count all matches, then load one sorted page of rows with their relations."""
    total = query.order_by(None).count()
    expr = _sort_expr(sort)
    # CASE instead of NULLS LAST, which MySQL does not support.
    missing_last = case((expr.is_(None), 1), else_=0)
    items = (
        query.options(*_event_load_options())
        .order_by(
            missing_last,
            expr.asc() if order == "asc" else expr.desc(),
            SeismicEvent.origin_time.desc(),
            SeismicEvent.id.desc(),
        )
        .offset(offset)
        .limit(limit)
        .all()
    )
    payload = {
        "items": [item.to_dict() for item in items],
        "total": total,
        "limit": limit,
        "offset": offset,
    }
    return marshal(payload, seismic_event_list_response_model), 200


@seismic_events_ns.route("/seismic_events/filter")
class SeismicEventsFilterApi(Resource):
    @seismic_events_ns.doc(security=JWT_OR_API_KEY)
    @seismic_events_ns.expect(seismic_event_filter_parser)
    @seismic_events_ns.response(200, "Success", seismic_event_list_response_model)
    @seismic_events_ns.response(400, "Validation Error", error_model)
    @seismic_events_ns.response(401, "Unauthorized", error_model)
    @seismic_events_ns.response(403, "Forbidden", error_model)
    @seismic_events_ns.response(404, "Not Found", error_model)
    def post(self):
        """Filter seismic events, newest first (requires can_event_view or can_event_edit).

        All body fields are optional. Returns at most `limit` items (default 100, max 200);
        `total` is the number of all matching events.
        """
        denied = _require_can_event_view()
        if denied:
            return denied

        payload = seismic_event_filter_parser.parse_args()
        limit, offset, error = _validated_page(payload)
        if error:
            return error
        query, error = _build_filtered_events_query(payload)
        if error:
            return error
        return _events_page(query, limit, offset, payload.get("sort"), payload.get("order"))


@seismic_events_ns.route("/seismic_events/magnitude_types")
class MagnitudeCatalogApi(Resource):
    @seismic_events_ns.doc(security=JWT_OR_API_KEY)
    @seismic_events_ns.response(200, "Success", magnitude_catalog_list_response_model)
    @seismic_events_ns.response(401, "Unauthorized", error_model)
    @seismic_events_ns.response(403, "Forbidden", error_model)
    def get(self):
        """List magnitude catalog types (requires can_event_view or can_event_edit)."""
        denied = _require_can_event_view()
        if denied:
            return denied

        items = Magnitude.query.order_by(Magnitude.code.asc()).all()
        payload = {"items": [item.to_dict() for item in items], "total": len(items)}
        return marshal(payload, magnitude_catalog_list_response_model), 200


@seismic_events_ns.route("/seismic_events/")
class SeismicEventsApi(Resource):
    @seismic_events_ns.doc(security=JWT_OR_API_KEY, parser=seismic_event_get_parser)
    @seismic_events_ns.response(200, "Success", seismic_event_list_response_model)
    @seismic_events_ns.response(400, "Validation Error", error_model)
    @seismic_events_ns.response(401, "Unauthorized", error_model)
    @seismic_events_ns.response(403, "Forbidden", error_model)
    def get(self):
        """Return the newest page of events. Query parameter is limit only."""
        denied = _require_can_event_view()
        if denied:
            return denied

        args = seismic_event_get_parser.parse_args()
        limit, offset, error = _validated_page(args)
        if error:
            return error
        return _events_page(SeismicEvent.query, limit, offset, args.get("sort"), args.get("order"))

    @seismic_events_ns.doc(security=JWT_OR_API_KEY)
    @seismic_events_ns.expect(seismic_event_create_parser)
    @seismic_events_ns.response(201, "Created", seismic_event_response_model)
    @seismic_events_ns.response(400, "Validation Error", error_model)
    @seismic_events_ns.response(401, "Unauthorized", error_model)
    @seismic_events_ns.response(403, "Forbidden", error_model)
    @seismic_events_ns.response(409, "Conflict", error_model)
    def post(self):
        """Create a seismic event (requires can_event_edit)."""
        denied = _require_can_event_edit()
        if denied:
            return denied

        payload = seismic_event_create_parser.parse_args()
        event = SeismicEvent()
        error = _apply_event_fields(event, payload, creating=True)
        if error:
            return error
        event.mark_created_by(resolve_actor())

        try:
            event.create()
        except IntegrityError:
            db.session.rollback()
            return {
                "error": "conflict",
                "message": "iesdata_id or seiscomp_oid is already registered.",
            }, 409
        except ValueError as err:
            db.session.rollback()
            return {"error": "validation_error", "message": str(err)}, 400

        logger.info("Seismic event created: event_id=%s", event.id)
        _maybe_sync_shakemap(event)
        return marshal(
            {"message": "Seismic event created successfully.", "event": event.to_dict()},
            seismic_event_response_model,
        ), 201


@seismic_events_ns.route("/seismic_events/seiscomp_oid=<path:seiscomp_oid>")
class SeismicEventBySeiscompApi(Resource):
    @seismic_events_ns.doc(security=JWT_OR_API_KEY)
    @seismic_events_ns.response(200, "Success", seismic_event_model)
    @seismic_events_ns.response(401, "Unauthorized", error_model)
    @seismic_events_ns.response(403, "Forbidden", error_model)
    @seismic_events_ns.response(404, "Not Found", error_model)
    def get(self, seiscomp_oid):
        """GET /api/seismic_events/seiscomp_oid=ies2026nrtc (exact match; `/` is allowed)"""
        denied = _require_can_event_view()
        if denied:
            return denied

        return _event_detail_or_404(_lookup_event(None, seiscomp_oid.strip(), None))


@seismic_events_ns.route("/seismic_events/iesdata_id=<int:iesdata_id>")
class SeismicEventByIesdataApi(Resource):
    @seismic_events_ns.doc(security=JWT_OR_API_KEY)
    @seismic_events_ns.response(200, "Success", seismic_event_model)
    @seismic_events_ns.response(401, "Unauthorized", error_model)
    @seismic_events_ns.response(403, "Forbidden", error_model)
    @seismic_events_ns.response(404, "Not Found", error_model)
    def get(self, iesdata_id):
        """GET /api/seismic_events/iesdata_id=539870"""
        denied = _require_can_event_view()
        if denied:
            return denied

        return _event_detail_or_404(_lookup_event(None, None, iesdata_id))


@seismic_events_ns.route("/seismic_events/event_id=<int:event_id>")
class SeismicEventDetailApi(Resource):
    @seismic_events_ns.doc(security=JWT_OR_API_KEY)
    @seismic_events_ns.response(200, "Success", seismic_event_model)
    @seismic_events_ns.response(401, "Unauthorized", error_model)
    @seismic_events_ns.response(403, "Forbidden", error_model)
    @seismic_events_ns.response(404, "Not Found", error_model)
    def get(self, event_id):
        """GET /api/seismic_events/event_id=12"""
        denied = _require_can_event_view()
        if denied:
            return denied

        return _event_detail_or_404(_lookup_event(event_id, None, None))

    @seismic_events_ns.doc(security=JWT_OR_API_KEY)
    @seismic_events_ns.expect(seismic_event_update_parser)
    @seismic_events_ns.response(200, "Success", seismic_event_response_model)
    @seismic_events_ns.response(400, "Validation Error", error_model)
    @seismic_events_ns.response(401, "Unauthorized", error_model)
    @seismic_events_ns.response(403, "Forbidden", error_model)
    @seismic_events_ns.response(404, "Not Found", error_model)
    @seismic_events_ns.response(409, "Conflict", error_model)
    def put(self, event_id):
        """Update a seismic event (requires can_event_edit)."""
        denied = _require_can_event_edit()
        if denied:
            return denied

        event, error = _get_event_or_404(event_id)
        if error:
            return error

        payload = seismic_event_update_parser.parse_args()
        apply_error = _apply_event_fields(event, payload, creating=False)
        if apply_error:
            db.session.rollback()
            return apply_error
        event.mark_updated_by(resolve_actor())

        try:
            event.save()
        except IntegrityError:
            db.session.rollback()
            return {
                "error": "conflict",
                "message": "iesdata_id or seiscomp_oid is already registered.",
            }, 409
        except ValueError as err:
            db.session.rollback()
            return {"error": "validation_error", "message": str(err)}, 400

        logger.info("Seismic event updated: event_id=%s", event.id)
        _maybe_sync_shakemap(event)
        return marshal(
            {"message": "Seismic event updated successfully.", "event": event.to_dict()},
            seismic_event_response_model,
        ), 200

    @seismic_events_ns.doc(security=JWT_OR_API_KEY)
    @seismic_events_ns.response(200, "Success", message_response_model)
    @seismic_events_ns.response(401, "Unauthorized", error_model)
    @seismic_events_ns.response(403, "Forbidden", error_model)
    @seismic_events_ns.response(404, "Not Found", error_model)
    @seismic_events_ns.response(409, "Conflict", error_model)
    def delete(self, event_id):
        """Delete a seismic event and related magnitudes/beachball (requires can_event_edit).

        Published events must be unpublished first.
        """
        denied = _require_can_event_edit()
        if denied:
            return denied

        event, error = _get_event_or_404(event_id)
        if error:
            return error

        if event.published_event is not None:
            return {
                "error": "conflict",
                "message": (
                    "This earthquake is published. Unpublish it first, "
                    "then delete it."
                ),
            }, 409

        event_id_value = event.id
        seiscomp_oid = event.seiscomp_oid
        event.delete()
        delete_beachball_image(event_id_value)
        _maybe_delete_shakemap(seiscomp_oid)
        logger.info("Seismic event deleted: event_id=%s", event_id_value)
        return marshal({"message": "Seismic event deleted successfully."}, message_response_model), 200


@seismic_events_ns.route("/seismic_events/<int:event_id>/magnitudes")
class EventMagnitudesApi(Resource):
    @seismic_events_ns.doc(security=JWT_OR_API_KEY)
    @seismic_events_ns.expect(event_magnitude_create_parser)
    @seismic_events_ns.response(201, "Created", event_magnitude_response_model)
    @seismic_events_ns.response(400, "Validation Error", error_model)
    @seismic_events_ns.response(401, "Unauthorized", error_model)
    @seismic_events_ns.response(403, "Forbidden", error_model)
    @seismic_events_ns.response(404, "Not Found", error_model)
    @seismic_events_ns.response(409, "Conflict", error_model)
    def post(self, event_id):
        """Add a magnitude to a seismic event (requires can_event_edit)."""
        denied = _require_can_event_edit()
        if denied:
            return denied

        event, error = _get_event_or_404(event_id)
        if error:
            return error

        payload = event_magnitude_create_parser.parse_args()
        magnitude, mag_error = _resolve_magnitude(
            magnitude_id=payload.get("magnitude_id"),
            magnitude_code=payload.get("magnitude_code"),
        )
        if mag_error:
            return mag_error

        value = payload.get("value")
        if value is None:
            return {"error": "validation_error", "message": "value is required."}, 400
        range_error = _magnitude_value_error(magnitude, value)
        if range_error:
            return range_error

        item = EventMagnitude(
            event_id=event.id,
            magnitude_id=magnitude.id,
            value=value,
        )
        event.mark_updated_by(resolve_actor())
        try:
            item.create()
        except IntegrityError:
            db.session.rollback()
            return {
                "error": "conflict",
                "message": "This magnitude type is already assigned to the event.",
            }, 409

        logger.info(
            "Event magnitude added: event_id=%s event_magnitude_id=%s",
            event.id,
            item.id,
        )
        _maybe_sync_shakemap(event)
        return marshal(
            {
                "message": "Event magnitude added successfully.",
                "event_magnitude": item.to_dict(),
            },
            event_magnitude_response_model,
        ), 201


@seismic_events_ns.route("/seismic_events/magnitudes/<int:event_magnitude_id>")
class EventMagnitudeDetailApi(Resource):
    @seismic_events_ns.doc(security=JWT_OR_API_KEY)
    @seismic_events_ns.expect(event_magnitude_update_parser)
    @seismic_events_ns.response(200, "Success", event_magnitude_response_model)
    @seismic_events_ns.response(400, "Validation Error", error_model)
    @seismic_events_ns.response(401, "Unauthorized", error_model)
    @seismic_events_ns.response(403, "Forbidden", error_model)
    @seismic_events_ns.response(404, "Not Found", error_model)
    @seismic_events_ns.response(409, "Conflict", error_model)
    def put(self, event_magnitude_id):
        """Update an event magnitude (requires can_event_edit)."""
        denied = _require_can_event_edit()
        if denied:
            return denied

        item = EventMagnitude.query.filter_by(id=event_magnitude_id).first()
        if not item:
            return {"error": "not_found", "message": "Event magnitude not found."}, 404

        payload = event_magnitude_update_parser.parse_args()
        if payload.get("magnitude_id") is not None or payload.get("magnitude_code") is not None:
            magnitude, mag_error = _resolve_magnitude(
                magnitude_id=payload.get("magnitude_id"),
                magnitude_code=payload.get("magnitude_code"),
            )
            if mag_error:
                return mag_error
        else:
            magnitude = item.magnitude

        value = payload["value"] if payload.get("value") is not None else item.value
        range_error = _magnitude_value_error(magnitude, value)
        if range_error:
            return range_error

        item.magnitude_id = magnitude.id
        item.value = value
        item.event.mark_updated_by(resolve_actor())

        try:
            item.save()
        except IntegrityError:
            db.session.rollback()
            return {
                "error": "conflict",
                "message": "This magnitude type is already assigned to the event.",
            }, 409

        logger.info("Event magnitude updated: event_magnitude_id=%s", item.id)
        _maybe_sync_shakemap(item.event)
        return marshal(
            {
                "message": "Event magnitude updated successfully.",
                "event_magnitude": item.to_dict(),
            },
            event_magnitude_response_model,
        ), 200

    @seismic_events_ns.doc(security=JWT_OR_API_KEY)
    @seismic_events_ns.response(200, "Success", message_response_model)
    @seismic_events_ns.response(401, "Unauthorized", error_model)
    @seismic_events_ns.response(403, "Forbidden", error_model)
    @seismic_events_ns.response(404, "Not Found", error_model)
    def delete(self, event_magnitude_id):
        """Delete an event magnitude (requires can_event_edit)."""
        denied = _require_can_event_edit()
        if denied:
            return denied

        item = EventMagnitude.query.filter_by(id=event_magnitude_id).first()
        if not item:
            return {"error": "not_found", "message": "Event magnitude not found."}, 404

        item_id = item.id
        item.event.mark_updated_by(resolve_actor())
        item.delete()
        logger.info("Event magnitude deleted: event_magnitude_id=%s", item_id)
        return marshal(
            {"message": "Event magnitude deleted successfully."},
            message_response_model,
        ), 200


@seismic_events_ns.route("/seismic_events/<int:event_id>/beachball")
class EventBeachballApi(Resource):
    @seismic_events_ns.doc(security=JWT_OR_API_KEY)
    @seismic_events_ns.response(200, "Success", event_beachball_model)
    @seismic_events_ns.response(401, "Unauthorized", error_model)
    @seismic_events_ns.response(403, "Forbidden", error_model)
    @seismic_events_ns.response(404, "Not Found", error_model)
    def get(self, event_id):
        """Get beachball for a seismic event (requires can_event_view or can_event_edit)."""
        denied = _require_can_event_view()
        if denied:
            return denied

        event, error = _get_event_or_404(event_id)
        if error:
            return error
        if not event.beachball:
            return {"error": "not_found", "message": "Beachball not found for this event."}, 404
        return marshal(event.beachball.to_dict(), event_beachball_model), 200

    @seismic_events_ns.doc(security=JWT_OR_API_KEY)
    @seismic_events_ns.expect(event_beachball_parser)
    @seismic_events_ns.response(201, "Created", event_beachball_response_model)
    @seismic_events_ns.response(400, "Validation Error", error_model)
    @seismic_events_ns.response(401, "Unauthorized", error_model)
    @seismic_events_ns.response(403, "Forbidden", error_model)
    @seismic_events_ns.response(404, "Not Found", error_model)
    @seismic_events_ns.response(409, "Conflict", error_model)
    def post(self, event_id):
        """Create beachball for a seismic event (requires can_event_edit)."""
        denied = _require_can_event_edit()
        if denied:
            return denied

        event, error = _get_event_or_404(event_id)
        if error:
            return error
        if event.beachball:
            return {
                "error": "conflict",
                "message": "Beachball already exists for this event. Use PUT to update.",
            }, 409

        payload = event_beachball_parser.parse_args()
        mechanism_error = _validate_beachball_mechanism_payload(payload)
        if mechanism_error:
            return mechanism_error

        beachball = EventBeachball(
            event_id=event.id,
            rake=payload.get("rake"),
            dip=payload.get("dip"),
            strike=payload.get("strike"),
            beachball_path=None,
        )
        event.mark_updated_by(resolve_actor())
        try:
            _apply_generated_beachball_path(beachball)
            beachball.create()
        except ValueError as err:
            db.session.rollback()
            return {"error": "validation_error", "message": str(err)}, 400
        except IntegrityError:
            db.session.rollback()
            return {
                "error": "conflict",
                "message": "Beachball already exists for this event. Use PUT to update.",
            }, 409
        except Exception as err:
            db.session.rollback()
            logger.exception("Beachball image generation failed: event_id=%s", event.id)
            return {
                "error": "generation_error",
                "message": f"Beachball image generation failed: {err}",
            }, 500

        logger.info("Beachball created: event_id=%s beachball_id=%s", event.id, beachball.id)
        return marshal(
            {"message": "Beachball created successfully.", "beachball": beachball.to_dict()},
            event_beachball_response_model,
        ), 201

    @seismic_events_ns.doc(security=JWT_OR_API_KEY)
    @seismic_events_ns.expect(event_beachball_parser)
    @seismic_events_ns.response(200, "Success", event_beachball_response_model)
    @seismic_events_ns.response(400, "Validation Error", error_model)
    @seismic_events_ns.response(401, "Unauthorized", error_model)
    @seismic_events_ns.response(403, "Forbidden", error_model)
    @seismic_events_ns.response(404, "Not Found", error_model)
    def put(self, event_id):
        """Update beachball for a seismic event (requires can_event_edit)."""
        denied = _require_can_event_edit()
        if denied:
            return denied

        event, error = _get_event_or_404(event_id)
        if error:
            return error
        if not event.beachball:
            return {"error": "not_found", "message": "Beachball not found for this event."}, 404

        payload = event_beachball_parser.parse_args()
        mechanism_error = _validate_beachball_mechanism_payload(payload)
        if mechanism_error:
            return mechanism_error

        beachball = event.beachball
        if payload.get("rake") is not None:
            beachball.rake = payload.get("rake")
        if payload.get("dip") is not None:
            beachball.dip = payload.get("dip")
        if payload.get("strike") is not None:
            beachball.strike = payload.get("strike")
        # beachball_path is server-generated; ignore any client-supplied path.
        event.mark_updated_by(resolve_actor())

        try:
            _apply_generated_beachball_path(beachball)
            beachball.save()
        except ValueError as err:
            db.session.rollback()
            return {"error": "validation_error", "message": str(err)}, 400
        except Exception as err:
            db.session.rollback()
            logger.exception("Beachball image generation failed: event_id=%s", event.id)
            return {
                "error": "generation_error",
                "message": f"Beachball angles updated but image generation failed: {err}",
            }, 500

        logger.info("Beachball updated: event_id=%s beachball_id=%s", event.id, beachball.id)
        return marshal(
            {"message": "Beachball updated successfully.", "beachball": beachball.to_dict()},
            event_beachball_response_model,
        ), 200

    @seismic_events_ns.doc(security=JWT_OR_API_KEY)
    @seismic_events_ns.response(200, "Success", message_response_model)
    @seismic_events_ns.response(401, "Unauthorized", error_model)
    @seismic_events_ns.response(403, "Forbidden", error_model)
    @seismic_events_ns.response(404, "Not Found", error_model)
    def delete(self, event_id):
        """Delete beachball for a seismic event (requires can_event_edit)."""
        denied = _require_can_event_edit()
        if denied:
            return denied

        event, error = _get_event_or_404(event_id)
        if error:
            return error
        if not event.beachball:
            return {"error": "not_found", "message": "Beachball not found for this event."}, 404

        beachball_id = event.beachball.id
        event.mark_updated_by(resolve_actor())
        event.beachball.delete()
        delete_beachball_image(event.id)
        logger.info("Beachball deleted: event_id=%s beachball_id=%s", event.id, beachball_id)
        return marshal({"message": "Beachball deleted successfully."}, message_response_model), 200


def _shakemap_error_response(exc):
    status = exc.status or 502
    if status == 400:
        return {"error": "validation_error", "message": str(exc)}, 400
    if status == 404:
        return {"error": "not_found", "message": str(exc)}, 404
    if status == 503:
        return {"error": "configuration_error", "message": str(exc)}, 503
    return {"error": "upstream_error", "message": str(exc)}, 502


@seismic_events_ns.route("/shakemap/view")
class ShakeMapViewApi(Resource):
    @seismic_events_ns.doc(security=JWT_OR_API_KEY)
    @seismic_events_ns.response(200, "Success")
    @seismic_events_ns.response(400, "Validation Error", error_model)
    @seismic_events_ns.response(401, "Unauthorized", error_model)
    @seismic_events_ns.response(403, "Forbidden", error_model)
    @seismic_events_ns.response(502, "Bad Gateway", error_model)
    @seismic_events_ns.response(503, "Configuration Error", error_model)
    def get(self):
        """Products for the details map. Missing ShakeMap files are omitted."""
        denied = _require_can_event_view()
        if denied:
            return denied

        seiscomp_oid = (request.args.get("seiscomp_oid") or "").strip()
        try:
            return load_view(seiscomp_oid)
        except ShakeMapError as exc:
            return _shakemap_error_response(exc)


@seismic_events_ns.route("/shakemap/product/<string:filename>")
class ShakeMapProductApi(Resource):
    @seismic_events_ns.doc(security=JWT_OR_API_KEY)
    @seismic_events_ns.response(200, "Success")
    @seismic_events_ns.response(400, "Validation Error", error_model)
    @seismic_events_ns.response(401, "Unauthorized", error_model)
    @seismic_events_ns.response(403, "Forbidden", error_model)
    @seismic_events_ns.response(404, "Not Found", error_model)
    @seismic_events_ns.response(502, "Bad Gateway", error_model)
    @seismic_events_ns.response(503, "Configuration Error", error_model)
    def get(self, filename):
        """Proxy one calculated ShakeMap product (requires can_event_view or can_event_edit)."""
        denied = _require_can_event_view()
        if denied:
            return denied

        seiscomp_oid = (request.args.get("seiscomp_oid") or "").strip()
        try:
            content, content_type = fetch_product(seiscomp_oid, filename)
        except ShakeMapError as exc:
            return _shakemap_error_response(exc)

        return Response(content, status=200, mimetype=content_type)
