import logging

from flask_restx import Resource, marshal
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

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
    seismic_event_filter_parser,
    event_magnitude_create_parser,
    event_magnitude_update_parser,
    event_beachball_parser,
)
from app.models import SeismicEvent, Magnitude, EventMagnitude, EventBeachball
from app.utils.auth_utils import require_permissions

logger = logging.getLogger("app.seismic_events")


def _require_can_event_view():
    return require_permissions("can_event_edit", "can_event_view")


def _require_can_event_edit():
    return require_permissions("can_event_edit")


def _get_event_or_404(event_id):
    event = SeismicEvent.query.filter_by(id=event_id).first()
    if not event:
        return None, ({"error": "not_found", "message": "Seismic event not found."}, 404)
    return event, None


def _optional_str(value):
    if value is None:
        return None
    text = str(value).strip()
    return text or None


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


def _apply_event_fields(event, payload, *, creating=False):
    if creating or payload.get("origin_time") is not None:
        if payload.get("origin_time") is None:
            return {"error": "validation_error", "message": "origin_time is required."}, 400
        event.origin_time = payload.get("origin_time")

    if creating or payload.get("latitude") is not None:
        if payload.get("latitude") is None:
            return {"error": "validation_error", "message": "latitude is required."}, 400
        event.latitude = float(payload.get("latitude"))

    if creating or payload.get("longitude") is not None:
        if payload.get("longitude") is None:
            return {"error": "validation_error", "message": "longitude is required."}, 400
        event.longitude = float(payload.get("longitude"))

    if "depth" in payload and payload.get("depth") is not None:
        event.depth = float(payload.get("depth"))
    elif creating:
        event.depth = None

    for field in ("iesdata_id", "seiscomp_oid", "location_ge", "location_en", "area"):
        if creating or field in payload:
            if payload.get(field) is not None:
                event.__setattr__(field, _optional_str(payload.get(field)))
            elif creating:
                event.__setattr__(field, None)

    if creating:
        event.is_automatic = bool(payload.get("is_automatic", False))
    elif "is_automatic" in payload and payload.get("is_automatic") is not None:
        event.is_automatic = bool(payload.get("is_automatic"))

    return None


def _build_filtered_events_query(payload):
    """Build a SeismicEvent query from optional filter args. Returns (query, error_tuple)."""
    event_id = payload.get("event_id")
    iesdata_id = _optional_str(payload.get("iesdata_id"))
    seiscomp_oid = _optional_str(payload.get("seiscomp_oid"))
    location = _optional_str(payload.get("location"))
    area = _optional_str(payload.get("area"))
    magnitude_code = _optional_str(payload.get("magnitude"))
    magnitude_min = payload.get("magnitude_min")
    magnitude_max = payload.get("magnitude_max")
    depth_min = payload.get("depth_min")
    depth_max = payload.get("depth_max")
    date_from = payload.get("date_from")
    date_to = payload.get("date_to")

    if magnitude_min is not None and magnitude_max is not None and magnitude_min > magnitude_max:
        return None, (
            {
                "error": "validation_error",
                "message": "magnitude_min cannot be greater than magnitude_max.",
            },
            400,
        )
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

    if iesdata_id is not None:
        query = query.filter(SeismicEvent.iesdata_id.ilike(f"%{iesdata_id}%"))

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

    needs_magnitude_join = (
        magnitude_code is not None
        or magnitude_min is not None
        or magnitude_max is not None
    )
    if needs_magnitude_join:
        query = query.join(EventMagnitude, EventMagnitude.event_id == SeismicEvent.id)
        if magnitude_code is not None:
            code = magnitude_code.upper()
            magnitude = Magnitude.query.filter_by(code=code).first()
            if not magnitude:
                return None, (
                    {
                        "error": "not_found",
                        "message": f"Magnitude catalog entry not found for code: {code}",
                    },
                    404,
                )
            query = query.filter(EventMagnitude.magnitude_id == magnitude.id)
        if magnitude_min is not None:
            query = query.filter(EventMagnitude.value >= magnitude_min)
        if magnitude_max is not None:
            query = query.filter(EventMagnitude.value <= magnitude_max)
        query = query.distinct()

    return query.order_by(SeismicEvent.origin_time.desc()), None


@seismic_events_ns.route("/filter")
class SeismicEventsFilterApi(Resource):
    @seismic_events_ns.doc(security=JWT_OR_API_KEY)
    @seismic_events_ns.expect(seismic_event_filter_parser)
    @seismic_events_ns.response(200, "Success", seismic_event_list_response_model)
    @seismic_events_ns.response(400, "Validation Error", error_model)
    @seismic_events_ns.response(401, "Unauthorized", error_model)
    @seismic_events_ns.response(403, "Forbidden", error_model)
    @seismic_events_ns.response(404, "Not Found", error_model)
    def post(self):
        """Filter seismic events (requires can_event_view or can_event_edit). All body fields are optional."""
        denied = _require_can_event_view()
        if denied:
            return denied

        payload = seismic_event_filter_parser.parse_args()
        query, error = _build_filtered_events_query(payload)
        if error:
            return error

        items = query.all()
        response = {"items": [item.to_dict() for item in items], "total": len(items)}
        return marshal(response, seismic_event_list_response_model), 200


@seismic_events_ns.route("/magnitude_types")
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


@seismic_events_ns.route("/")
class SeismicEventsApi(Resource):
    @seismic_events_ns.doc(security=JWT_OR_API_KEY)
    @seismic_events_ns.response(200, "Success", seismic_event_list_response_model)
    @seismic_events_ns.response(401, "Unauthorized", error_model)
    @seismic_events_ns.response(403, "Forbidden", error_model)
    def get(self):
        """List seismic events (requires can_event_view or can_event_edit)."""
        denied = _require_can_event_view()
        if denied:
            return denied

        items = SeismicEvent.query.order_by(SeismicEvent.origin_time.desc()).all()
        payload = {"items": [item.to_dict() for item in items], "total": len(items)}
        return marshal(payload, seismic_event_list_response_model), 200

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
        return marshal(
            {"message": "Seismic event created successfully.", "event": event.to_dict()},
            seismic_event_response_model,
        ), 201


@seismic_events_ns.route("/<int:event_id>")
class SeismicEventDetailApi(Resource):
    @seismic_events_ns.doc(security=JWT_OR_API_KEY)
    @seismic_events_ns.response(200, "Success", seismic_event_model)
    @seismic_events_ns.response(401, "Unauthorized", error_model)
    @seismic_events_ns.response(403, "Forbidden", error_model)
    @seismic_events_ns.response(404, "Not Found", error_model)
    def get(self, event_id):
        """Get a seismic event by id (requires can_event_view or can_event_edit)."""
        denied = _require_can_event_view()
        if denied:
            return denied

        event, error = _get_event_or_404(event_id)
        if error:
            return error
        return marshal(event.to_dict(), seismic_event_model), 200

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
        # RequestParser always returns declared keys; treat only provided non-None as updates
        # except empty strings for optional text fields which clear via _optional_str when key present.
        update_payload = {}
        for key, value in payload.items():
            if value is not None:
                update_payload[key] = value

        apply_error = _apply_event_fields(event, update_payload, creating=False)
        if apply_error:
            return apply_error

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
        return marshal(
            {"message": "Seismic event updated successfully.", "event": event.to_dict()},
            seismic_event_response_model,
        ), 200

    @seismic_events_ns.doc(security=JWT_OR_API_KEY)
    @seismic_events_ns.response(200, "Success", message_response_model)
    @seismic_events_ns.response(401, "Unauthorized", error_model)
    @seismic_events_ns.response(403, "Forbidden", error_model)
    @seismic_events_ns.response(404, "Not Found", error_model)
    def delete(self, event_id):
        """Delete a seismic event and related magnitudes/beachball (requires can_event_edit)."""
        denied = _require_can_event_edit()
        if denied:
            return denied

        event, error = _get_event_or_404(event_id)
        if error:
            return error

        event_id_value = event.id
        event.delete()
        logger.info("Seismic event deleted: event_id=%s", event_id_value)
        return marshal({"message": "Seismic event deleted successfully."}, message_response_model), 200


@seismic_events_ns.route("/<int:event_id>/magnitudes")
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

        item = EventMagnitude(
            event_id=event.id,
            magnitude_id=magnitude.id,
            value=float(value),
        )
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
        return marshal(
            {
                "message": "Event magnitude added successfully.",
                "event_magnitude": item.to_dict(),
            },
            event_magnitude_response_model,
        ), 201


@seismic_events_ns.route("/magnitudes/<int:event_magnitude_id>")
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
        if payload.get("value") is not None:
            item.value = float(payload.get("value"))

        if payload.get("magnitude_id") is not None or payload.get("magnitude_code") is not None:
            magnitude, mag_error = _resolve_magnitude(
                magnitude_id=payload.get("magnitude_id"),
                magnitude_code=payload.get("magnitude_code"),
            )
            if mag_error:
                return mag_error
            item.magnitude_id = magnitude.id

        try:
            item.save()
        except IntegrityError:
            db.session.rollback()
            return {
                "error": "conflict",
                "message": "This magnitude type is already assigned to the event.",
            }, 409

        logger.info("Event magnitude updated: event_magnitude_id=%s", item.id)
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
        item.delete()
        logger.info("Event magnitude deleted: event_magnitude_id=%s", item_id)
        return marshal(
            {"message": "Event magnitude deleted successfully."},
            message_response_model,
        ), 200


@seismic_events_ns.route("/<int:event_id>/beachball")
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
        beachball = EventBeachball(
            event_id=event.id,
            rake=payload.get("rake"),
            dip=payload.get("dip"),
            strike=payload.get("strike"),
            beachball_path=_optional_str(payload.get("beachball_path")),
        )
        try:
            beachball.create()
        except IntegrityError:
            db.session.rollback()
            return {
                "error": "conflict",
                "message": "Beachball already exists for this event. Use PUT to update.",
            }, 409

        logger.info("Beachball created: event_id=%s beachball_id=%s", event.id, beachball.id)
        return marshal(
            {"message": "Beachball created successfully.", "beachball": beachball.to_dict()},
            event_beachball_response_model,
        ), 201

    @seismic_events_ns.doc(security=JWT_OR_API_KEY)
    @seismic_events_ns.expect(event_beachball_parser)
    @seismic_events_ns.response(200, "Success", event_beachball_response_model)
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
        beachball = event.beachball
        if payload.get("rake") is not None:
            beachball.rake = payload.get("rake")
        if payload.get("dip") is not None:
            beachball.dip = payload.get("dip")
        if payload.get("strike") is not None:
            beachball.strike = payload.get("strike")
        if payload.get("beachball_path") is not None:
            beachball.beachball_path = _optional_str(payload.get("beachball_path"))
        beachball.save()

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
        event.beachball.delete()
        logger.info("Beachball deleted: event_id=%s beachball_id=%s", event.id, beachball_id)
        return marshal({"message": "Beachball deleted successfully."}, message_response_model), 200
