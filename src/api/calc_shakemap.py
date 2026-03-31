from flask_restx import Resource
from flask import request

from src.api.nsmodels import shakemap_ns, shakemap_parser, shakemap_model
from src.models.seismic_event import SeismicEvent
from src.workers.run_shakemap import run_shakemap_worker
from src.config import Config

@shakemap_ns.route("/run_shakemap")
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

    @shakemap_ns.expect(shakemap_model)
    @shakemap_ns.doc(security='ApiKeyAuth', description='Create or update a seismic event (requires X-API-Key)')
    def post(self):

        # --- Auth check ---
        api_key = request.headers.get('X-API-Key')
        if api_key != Config.API_KEY:
            return {'error': 'Unauthorized - Invalid API key'}, 401

        
        # გამოიყენე parser
        args = shakemap_parser.parse_args()
        seiscomp_oid = args["seiscomp_oid"]

        if not seiscomp_oid:
            return {"error": "seiscomp_oid required"}, 400

        # DB query to get event data
        event = SeismicEvent.query.filter_by(seiscomp_oid=seiscomp_oid).first()
        if not event:
            return {"error": f"Event {seiscomp_oid} not found"}, 404

        parsed_data = {
            "event_id": seiscomp_oid,
            "time": event.origin_time.isoformat(),
            "longitude": event.longitude,
            "latitude": event.latitude,
            "depth": event.depth,
            "ml": event.ml,
            "desc": event.region_ge or "Event Description"
        }

        try:
            result = run_shakemap_worker(parsed_data)
            event.shakemap_calculated = True
            event.save()
            return result, 200
        except Exception as e:
            return {
                "status": "failed",
                "event_id": seiscomp_oid,
                "error": str(e)
            }, 500