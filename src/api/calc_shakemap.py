import os
import logging

from flask_restx import Resource
from flask import request, send_file
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

from src.api.nsmodels import shakemap_ns, shakemap_parser, shakemap_model
from src.models.seismic_event import SeismicEvent
from src.workers.run_shakemap import run_shakemap_worker
from src.config import Config

SHAKEMAP_BASE_PATH = Config.SHAKEMAP_BASE_PATH
# დაშვებული სურათების ტიპები
ALLOWED_IMAGES = {
    "pga": "pga.jpg",
    "intensity": "intensity.jpg",
    "pgv": "pgv.jpg",
}

logger = logging.getLogger("app.shakemap")


def get_products_path(seiscomp_oid, event_id=None):
    """products ბილიკს ჯერ OID-ით ეძებს, შემდეგ რიცხვითი event_id-ით."""
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
        # 1) შიდა სერვისის ავტორიზაცია API key-ით
        api_key = request.headers.get('X-API-Key')
        if api_key and api_key == Config.API_KEY:
            return True

        # 2) მომხმარებლის ავტორიზაცია JWT Bearer ტოკენით
        try:
            verify_jwt_in_request()
            identity = get_jwt_identity()
            return bool(identity)
        except Exception:
            return False

    @shakemap_ns.doc(parser=shakemap_parser)
    @shakemap_ns.doc(
        security=[{'ApiKeyAuth': []}, {'JsonWebToken': []}],
        description='ShakeMap-ის გაშვება შესაძლებელია X-API-Key-ით ან JWT Bearer ტოკენით',
    )
    def post(self):
        # --- მოთხოვნის body-ის დამუშავება ---
        args = shakemap_parser.parse_args()
        seiscomp_oid = args["seiscomp_oid"]
        # --- ავტორიზაციის შემოწმება ---
        if not self._is_authorized():
            logger.warning("ShakeMap run denied: seiscomp_oid=%s unauthorized", seiscomp_oid)
            return {'error': 'არ გაქვს წვდომა. მიუთითე სწორი X-API-Key ან JWT ტოკენი.'}, 401

        try:
            # --- მოვლენის მოძებნა seiscomp_oid-ით ---
            event = SeismicEvent.query.filter_by(seiscomp_oid=seiscomp_oid).first()
            if not event:
                logger.info("ShakeMap run failed: seiscomp_oid=%s not found", seiscomp_oid)
                return {"error": f"მოვლენა ვერ მოიძებნა: {seiscomp_oid}"}, 404

            parsed_data = {
                "event_id": event.event_id,
                "time": event.origin_time.isoformat(),
                "longitude": event.longitude,
                "latitude": event.latitude,
                "depth": event.depth,
                "ml": event.ml,
                "desc": event.region_ge or "მოვლენის აღწერა"
            }

            # --- ShakeMap worker-ის გაშვება ---
            result = run_shakemap_worker(parsed_data)
            # --- მოვლენის shakemap_calculated სტატუსის განახლება ---
            event.shakemap_calculated = True
            # --- მოვლენის შენახვა ---
            event.save()
            logger.info(
                "ShakeMap run success: seiscomp_oid=%s event_id=%s",
                seiscomp_oid,
                event.event_id,
            )
            # --- შედეგის დაბრუნება ---
            return result, 200
        except ValueError as e:
            logger.info("ShakeMap run failed: seiscomp_oid=%s value error=%s", seiscomp_oid, e)
            return {"error": str(e)}, 404
        except Exception as e:
            logger.exception("ShakeMap run exception: seiscomp_oid=%s", seiscomp_oid)
            return {
                "status": "წარუმატებელია",
                "event_id": seiscomp_oid,
                "error": str(e)
            }, 500


# --- ShakeMap შედეგები ---
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
        """აბრუნებს კონკრეტული მოვლენის ShakeMap პროდუქტებს."""
        event = SeismicEvent.query.filter_by(seiscomp_oid=seiscomp_oid).first()
        if not event:
            logger.info("ShakeMap results failed: seiscomp_oid=%s not found", seiscomp_oid)
            return {"error": f"მოვლენა ვერ მოიძებნა: {seiscomp_oid}"}, 404

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
            "status": "წარმატებულია",
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
        """აბრუნებს ShakeMap სურათს SeisComP OID-ის მიხედვით."""
        event = SeismicEvent.query.filter_by(seiscomp_oid=seiscomp_oid).first()
        if not event:
            logger.info("ShakeMap image failed: seiscomp_oid=%s event not found", seiscomp_oid)
            return {"error": f"მოვლენა ვერ მოიძებნა: {seiscomp_oid}"}, 404

        filename = ALLOWED_IMAGES.get(image_type)
        if not filename:
            logger.info(
                "ShakeMap image failed: seiscomp_oid=%s unsupported image_type=%s",
                seiscomp_oid,
                image_type,
            )
            return {"error": f"სურათის ტიპი არ არის მხარდაჭერილი: {image_type}"}, 400

        products_path = get_products_path(seiscomp_oid, event.event_id)
        file_path = os.path.join(products_path, filename)
        if not os.path.exists(file_path):
            logger.info(
                "ShakeMap image failed: seiscomp_oid=%s missing file=%s",
                seiscomp_oid,
                filename,
            )
            return {"error": f"სურათი ვერ მოიძებნა: {filename}"}, 404

        logger.info(
            "ShakeMap image success: seiscomp_oid=%s image_type=%s",
            seiscomp_oid,
            image_type,
        )
        return send_file(file_path, mimetype="image/jpeg")