import os
import logging
from datetime import datetime, timezone

from flask_restx import Resource
from flask import request, send_file
from flask_jwt_extended import get_jwt_identity

from src.utils import is_authorized_request
from src.api.nsmodels import shakemap_ns, shakemap_parser, shakemap_model
from src.models import SeismicEvent, ShakemapJob
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
        if not is_authorized_request():
            logger.warning("ShakeMap run denied: seiscomp_oid=%s unauthorized", seiscomp_oid)
            return {'error': 'არ გაქვს წვდომა. მიუთითე სწორი X-API-Key ან JWT ტოკენი.'}, 401

        try:
            # --- მოვლენის მოძებნა seiscomp_oid-ით ---
            event = SeismicEvent.query.filter_by(seiscomp_oid=seiscomp_oid).first()
            if not event:
                logger.info("ShakeMap run failed: seiscomp_oid=%s not found", seiscomp_oid)
                return {"error": f"მოვლენა ვერ მოიძებნა: {seiscomp_oid}"}, 404

            shakemap_job = ShakemapJob.query.filter_by(seiscomp_oid=seiscomp_oid).first()
            user_uuid = get_jwt_identity()
            if not shakemap_job:
                shakemap_job = ShakemapJob(seiscomp_oid=seiscomp_oid, uuid=user_uuid)
                shakemap_job.create()

            if shakemap_job.status == "running":
                logger.info("ShakeMap run failed: seiscomp_oid=%s already running", seiscomp_oid)
                return {"error": f"მოვლენა უკვე გამშვებია: {seiscomp_oid}"}, 400

            shakemap_job.status = "running"
            shakemap_job.started_at = datetime.now(timezone.utc)
            shakemap_job.save()

            parsed_data = {
                "seiscomp_oid": seiscomp_oid,
                "time": event.origin_time.isoformat(),
                "longitude": event.longitude,
                "latitude": event.latitude,
                "depth": event.depth,
                "ml": event.ml,
                "desc": event.region_ge or "მოვლენის აღწერა"
            }

            # --- ShakeMap worker-ის გაშვება ---
            result = run_shakemap_worker(parsed_data)
            # --- წარმატებული დათვლის შემდეგ სტატუსის განახლება ---
            shakemap_job.status = "generated"
            shakemap_job.finished_at = datetime.now(timezone.utc)
            shakemap_job.save()

            # --- მოვლენის შენახვა ---
            event.save()
            logger.info("ShakeMap run success: seiscomp_oid=%s", seiscomp_oid)
            
            # --- შედეგის დაბრუნება ---
            return result, 200
        except ValueError as e:
            shakemap_job = SeismicEvent.query.filter_by(seiscomp_oid=seiscomp_oid).first()
            if shakemap_job:
                shakemap_job.status = "failed"
                shakemap_job.finished_at = datetime.now(timezone.utc)
                shakemap_job.save()
            logger.info("ShakeMap run failed: seiscomp_oid=%s value error=%s", seiscomp_oid, e)
            return {"error": str(e)}, 404
        except Exception as e:
            shakemap_job = ShakemapJob.query.filter_by(seiscomp_oid=seiscomp_oid).first()
            if shakemap_job:
                shakemap_job.status = "failed"
                shakemap_job.finished_at = datetime.now(timezone.utc)
                shakemap_job.save()
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
        shakemap_job = ShakemapJob.query.filter_by(seiscomp_oid=seiscomp_oid).first()
        if not shakemap_job:
            logger.info("ShakeMap results failed: seiscomp_oid=%s not found", seiscomp_oid)
            return {"error": f"მოვლენა ვერ მოიძებნა: {seiscomp_oid}"}, 404

        products_path = f"{SHAKEMAP_BASE_PATH}/{seiscomp_oid}/current/products" if seiscomp_oid else None
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

        products_path = f'{SHAKEMAP_BASE_PATH}/{seiscomp_oid}/current/products'
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