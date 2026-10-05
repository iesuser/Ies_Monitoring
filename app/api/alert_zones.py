import logging

from flask import request
from flask_restx import Resource, inputs, marshal

from app.api.nsmodels import (
    alert_zones_ns,
    alert_zone_model,
    alert_zone_create_model,
    alert_zone_update_model,
    alert_zone_response_model,
    alert_zone_list_response_model,
    alert_zone_message_response_model,
    alert_zone_error_model,
    ALERT_ZONES_JWT_OR_API_KEY,
)
from app.models import AlertZone
from app.utils.auth_utils import require_permissions, resolve_actor
from app.utils.validators import validate_polygon_geometry

logger = logging.getLogger("app.alert_zones")

# Allowed range for ML (local magnitude) thresholds
MAGNITUDE_RANGE = (0.0, 10.0)


def _require_alert_zones_read():
    return require_permissions("can_recips", "can_recips_read")


def _require_alert_zones_write():
    return require_permissions("can_recips")


def _get_zone_or_404(zone_id):
    zone = AlertZone.query.filter_by(id=zone_id).first()
    if not zone:
        return None, ({"error": "not_found", "message": "Alert zone not found."}, 404)
    return zone, None


def _parse_name(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("name cannot be empty.")
    name = value.strip()
    if len(name) > 255:
        raise ValueError("name must be at most 255 characters.")
    return name


def _parse_magnitude(value, field_name):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be a number.")
    low, high = MAGNITUDE_RANGE
    if not low <= value <= high:
        raise ValueError(f"{field_name} must be between {low} and {high}.")
    return float(value)


def _parse_max_magnitude(value):
    if value is None:
        return None
    return _parse_magnitude(value, "max_magnitude")


def _magnitude_range_error(min_magnitude, max_magnitude):
    if max_magnitude is not None and max_magnitude < min_magnitude:
        return {
            "error": "validation_error",
            "message": "max_magnitude must be greater than or equal to min_magnitude.",
        }, 400
    return None


def _parse_bool(value, field_name):
    try:
        return inputs.boolean(value)
    except ValueError:
        raise ValueError(f"{field_name} must be a boolean.")


def _parse_notif_channels(value):
    if not isinstance(value, list) or not value:
        raise ValueError("notif_channels must be a non-empty list.")

    channels = []
    for channel in value:
        if channel not in AlertZone.NOTIF_CHANNELS:
            allowed = ", ".join(AlertZone.NOTIF_CHANNELS)
            raise ValueError(f"Unknown notification channel: {channel!r}. Allowed: {allowed}.")
        if channel not in channels:
            channels.append(channel)
    return channels


def _parse_zone_payload(partial):
    """
    Validate the JSON body. Required fields are enforced only when partial is False.

    Returns:
        (values, None) on success
        (None, (error_body, status_code)) on validation failure
    """
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None, ({"error": "validation_error", "message": "Request body must be a JSON object."}, 400)

    parsers = {
        "name": _parse_name,
        "geometry": validate_polygon_geometry,
        "min_magnitude": lambda value: _parse_magnitude(value, "min_magnitude"),
        "max_magnitude": _parse_max_magnitude,
        "notif_channels": _parse_notif_channels,
        "enabled": lambda value: _parse_bool(value, "enabled"),
        "notif_is_staff": lambda value: _parse_bool(value, "notif_is_staff"),
    }
    required = {"name", "geometry", "min_magnitude", "notif_channels"}

    values = {}
    try:
        for field_name, parse in parsers.items():
            if field_name in data:
                values[field_name] = parse(data[field_name])
            elif not partial and field_name in required:
                raise ValueError(f"{field_name} is required.")
    except ValueError as err:
        return None, ({"error": "validation_error", "message": str(err)}, 400)

    return values, None


@alert_zones_ns.route("/alert_zones")
class AlertZonesApi(Resource):
    @alert_zones_ns.doc(security=ALERT_ZONES_JWT_OR_API_KEY)
    @alert_zones_ns.response(200, "Success", alert_zone_list_response_model)
    @alert_zones_ns.response(401, "Unauthorized", alert_zone_error_model)
    @alert_zones_ns.response(403, "Forbidden", alert_zone_error_model)
    def get(self):
        """List alert zones (JWT or API key with can_recips / can_recips_read)."""
        denied = _require_alert_zones_read()
        if denied:
            return denied

        items = AlertZone.query.order_by(AlertZone.id.asc()).all()
        payload = {"items": [item.to_dict() for item in items], "total": len(items)}
        return marshal(payload, alert_zone_list_response_model), 200

    @alert_zones_ns.doc(security=ALERT_ZONES_JWT_OR_API_KEY)
    @alert_zones_ns.expect(alert_zone_create_model)
    @alert_zones_ns.response(201, "Created", alert_zone_response_model)
    @alert_zones_ns.response(400, "Validation Error", alert_zone_error_model)
    @alert_zones_ns.response(401, "Unauthorized", alert_zone_error_model)
    @alert_zones_ns.response(403, "Forbidden", alert_zone_error_model)
    def post(self):
        """Create an alert zone (JWT or API key with can_recips)."""
        denied = _require_alert_zones_write()
        if denied:
            return denied

        actor = resolve_actor()
        values, error = _parse_zone_payload(partial=False)
        if error:
            return error

        error = _magnitude_range_error(values["min_magnitude"], values.get("max_magnitude"))
        if error:
            return error

        zone = AlertZone(
            **values,
            created_by_user_id=actor["user_id"],
            updated_by_user_id=actor["user_id"],
        )
        zone.create()

        logger.info("Alert zone created: actor=%s zone_id=%s", actor["label"], zone.id)
        return marshal(
            {"message": "Alert zone created successfully.", "alert_zone": zone.to_dict()},
            alert_zone_response_model,
        ), 201


@alert_zones_ns.route("/alert_zones/<int:zone_id>")
class AlertZoneDetailApi(Resource):
    @alert_zones_ns.doc(security=ALERT_ZONES_JWT_OR_API_KEY)
    @alert_zones_ns.response(200, "Success", alert_zone_model)
    @alert_zones_ns.response(401, "Unauthorized", alert_zone_error_model)
    @alert_zones_ns.response(403, "Forbidden", alert_zone_error_model)
    @alert_zones_ns.response(404, "Not Found", alert_zone_error_model)
    def get(self, zone_id):
        """Get an alert zone by id (JWT or API key with can_recips / can_recips_read)."""
        denied = _require_alert_zones_read()
        if denied:
            return denied

        zone, error = _get_zone_or_404(zone_id)
        if error:
            return error
        return marshal(zone.to_dict(), alert_zone_model), 200

    @alert_zones_ns.doc(security=ALERT_ZONES_JWT_OR_API_KEY)
    @alert_zones_ns.expect(alert_zone_update_model)
    @alert_zones_ns.response(200, "Success", alert_zone_response_model)
    @alert_zones_ns.response(400, "Validation Error", alert_zone_error_model)
    @alert_zones_ns.response(401, "Unauthorized", alert_zone_error_model)
    @alert_zones_ns.response(403, "Forbidden", alert_zone_error_model)
    @alert_zones_ns.response(404, "Not Found", alert_zone_error_model)
    def put(self, zone_id):
        """Update an alert zone by id; only provided fields change (JWT or API key with can_recips)."""
        denied = _require_alert_zones_write()
        if denied:
            return denied

        actor = resolve_actor()
        zone, error = _get_zone_or_404(zone_id)
        if error:
            return error

        values, error = _parse_zone_payload(partial=True)
        if error:
            return error

        error = _magnitude_range_error(
            values.get("min_magnitude", zone.min_magnitude),
            values.get("max_magnitude", zone.max_magnitude),
        )
        if error:
            return error

        for field_name, value in values.items():
            setattr(zone, field_name, value)
        zone.updated_by_user_id = actor["user_id"]
        zone.save()

        logger.info("Alert zone updated: actor=%s zone_id=%s", actor["label"], zone.id)
        return marshal(
            {"message": "Alert zone updated successfully.", "alert_zone": zone.to_dict()},
            alert_zone_response_model,
        ), 200

    @alert_zones_ns.doc(security=ALERT_ZONES_JWT_OR_API_KEY)
    @alert_zones_ns.response(200, "Success", alert_zone_message_response_model)
    @alert_zones_ns.response(401, "Unauthorized", alert_zone_error_model)
    @alert_zones_ns.response(403, "Forbidden", alert_zone_error_model)
    @alert_zones_ns.response(404, "Not Found", alert_zone_error_model)
    def delete(self, zone_id):
        """Delete an alert zone (JWT or API key with can_recips)."""
        denied = _require_alert_zones_write()
        if denied:
            return denied

        actor = resolve_actor()
        zone, error = _get_zone_or_404(zone_id)
        if error:
            return error

        zone_id_value = zone.id
        zone.delete()
        logger.info("Alert zone deleted: actor=%s zone_id=%s", actor["label"], zone_id_value)
        return marshal({"message": "Alert zone deleted successfully."}, alert_zone_message_response_model), 200
