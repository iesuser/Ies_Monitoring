from flask_restx import Resource
from flask import request
import os

from src.api.nsmodels import shakemap_ns, shakemap_model
from src.models.seismic_event import SeismicEvent
from src.workers.run_shakemap import run_shakemap_worker

@shakemap_ns.route("/run_shakemap")
class RunShakeMap(Resource):

    @shakemap_ns.expect(shakemap_model)
    def post(self):

        # API Key check
        api_key = request.headers.get("X-API-KEY")
        if api_key != os.getenv("SHAKEMAP_API_KEY", "super-secret-key"):
            return {"error": "Unauthorized"}, 401

        data = request.json
        seiscomp_oid = data.get("seiscomp_oid")

        if not seiscomp_oid:
            return {"error": "seiscomp_oid required"}, 400

        # 1️⃣ DB query to get event data
        event = SeismicEvent.query.filter_by(seiscomp_oid=seiscomp_oid).first()
        if not event:
            return {"error": f"Event {seiscomp_oid} not found"}, 404

        parsed_data = {
            "event_id": seiscomp_oid,
            "time": event.origin_time.isoformat(),
            "longitude": event.longitude,
            "latitude": event.latitude,
            "depth_km": event.depth_km,
            "magnitude": event.magnitude
        }

        # 2️⃣ Run async worker
        run_shakemap_worker(parsed_data)

        return {"status": "started", "event_id": seiscomp_oid}, 202