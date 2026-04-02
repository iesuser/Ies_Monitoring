import os

from flask_restx import Resource
from flask import request, send_file
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

from src.api.nsmodels import shakemap_ns, shakemap_parser, shakemap_model
from src.models.seismic_event import SeismicEvent
from src.workers.run_shakemap import run_shakemap_worker
from src.config import Config

SHAKEMAP_BASE_PATH = Config.SHAKEMAP_BASE_PATH
# Allowed images
ALLOWED_IMAGES = {
    "pga": "pga.jpg",
    "intensity": "intensity.jpg",
    "pgv": "pgv.jpg",
}


def get_products_path(seiscomp_oid, event_id=None):
    """Resolve products path by OID first, then numeric event_id."""
    candidates = [
        f"{SHAKEMAP_BASE_PATH}/{seiscomp_oid}/current/products" if seiscomp_oid else None
    ]
    if event_id is not None:
        candidates.append(f"{SHAKEMAP_BASE_PATH}/{event_id}/current/products")

    for path in candidates:
        if path and os.path.isdir(path):
            return path

    return candidates[0]

@shakemap_ns.route("/shakemap")
@shakemap_ns.doc(
    responses={
        200: 'OK',
        201: 'Created',
        400: 'Invalid Argument',
        401: 'Unauthorized',
        404: 'Not Found'
    }
)
class RunShakeMap(Resource):
    @staticmethod
    def _is_authorized():
        # 1) Internal service auth via API key
        api_key = request.headers.get('X-API-Key')
        if api_key and api_key == Config.API_KEY:
            return True

        # 2) User auth via JWT Bearer token
        try:
            verify_jwt_in_request()
            identity = get_jwt_identity()
            return bool(identity)
        except Exception:
            return False

    @shakemap_ns.expect(shakemap_model)
    @shakemap_ns.doc(
        security=[{'ApiKeyAuth': []}, {'JsonWebToken': []}],
        description='Trigger ShakeMap by using either X-API-Key or JWT Bearer token'
    )
    def post(self):
        # --- Parse request body ---
        args = shakemap_parser.parse_args()
        seiscomp_oid = args["seiscomp_oid"]
        # --- Auth check ---
        if not self._is_authorized():
            return {'error': 'Unauthorized - provide valid X-API-Key or JWT token'}, 401

        try:
            # --- Get event by seiscomp_oid ---
            event = SeismicEvent.query.filter_by(seiscomp_oid=seiscomp_oid).first()
            if not event:
                return {"error": f"Event {seiscomp_oid} not found"}, 404

            parsed_data = {
                "event_id": event.event_id,
                "time": event.origin_time.isoformat(),
                "longitude": event.longitude,
                "latitude": event.latitude,
                "depth": event.depth,
                "ml": event.ml,
                "desc": event.region_ge or "Event Description"
            }

            # --- Run ShakeMap worker ---
            result = run_shakemap_worker(parsed_data)
            # --- Update event shakemap_calculated status ---
            event.shakemap_calculated = True
            # --- Save event ---
            event.save()
            # --- Return result ---
            return result, 200
        except ValueError as e:
            return {"error": str(e)}, 404
        except Exception as e:
            return {
                "status": "failed",
                "event_id": seiscomp_oid,
                "error": str(e)
            }, 500


# --- ShakeMap results ---
@shakemap_ns.route("/shakemap/<string:seiscomp_oid>")
@shakemap_ns.doc(
    params={
        "seiscomp_oid": "SeisComP Event OID",
    },
    responses={
        200: 'OK',
        400: 'Invalid Argument',
        404: 'Not Found'
    }
)
class ShakeMapResults(Resource):
    def get(self, seiscomp_oid):
        """Return ShakeMap products for an event."""
        event = SeismicEvent.query.filter_by(seiscomp_oid=seiscomp_oid).first()
        if not event:
            return {"error": f"Event {seiscomp_oid} not found"}, 404

        products_path = get_products_path(seiscomp_oid, event.event_id)
        images = []
        for key, filename in ALLOWED_IMAGES.items():
            file_path = os.path.join(products_path, filename)
            images.append(
                {
                    "type": key,
                    "filename": filename,
                    "exists": os.path.exists(file_path),
                    "url": f"/api/shakemap/{seiscomp_oid}/image/{key}",
                }
            )

        return {
            "status": "success",
            "event_id": seiscomp_oid,
            "products_path": products_path,
            "images": images,
        }, 200


@shakemap_ns.route("/shakemap/<string:seiscomp_oid>/image/<string:image_type>")
@shakemap_ns.doc(
    params={
        "seiscomp_oid": "SeisComP Event OID",
        "image_type": "ShakeMap image type: pga, pgv, intensity",
    },
    responses={
        200: 'OK',
        400: 'Invalid Argument',
        404: 'Not Found'
    }
)
class ShakeMapResultImage(Resource):
    def get(self, seiscomp_oid, image_type):
        """Return a ShakeMap image file by SeisComP OID."""
        event = SeismicEvent.query.filter_by(seiscomp_oid=seiscomp_oid).first()
        if not event:
            return {"error": f"Event {seiscomp_oid} not found"}, 404

        filename = ALLOWED_IMAGES.get(image_type)
        if not filename:
            return {"error": f"Unsupported image type: {image_type}"}, 400

        products_path = get_products_path(seiscomp_oid, event.event_id)
        file_path = os.path.join(products_path, filename)
        if not os.path.exists(file_path):
            return {"error": f"Image not found: {filename}"}, 404

        return send_file(file_path, mimetype="image/jpeg")