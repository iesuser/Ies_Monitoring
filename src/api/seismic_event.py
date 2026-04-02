from flask_restx import Resource
from flask import request
import datetime

from src.api.nsmodels import event_ns, event_model, event_parser
from src.models import SeismicEvent
from src.config import Config

@event_ns.route('/events')
@event_ns.doc(
    responses={
        200: 'OK',
        201: 'Created',
        400: 'Invalid Argument',
        401: 'Unauthorized',
        404: 'Not Found'
    }
)
class SeismicListAPI(Resource):
    @event_ns.marshal_list_with(event_model)  # show schema in Swagger
    def get(self):
        """List all seismic events"""
        events = SeismicEvent.query.all()
        if not events:
            return {"error": "მიწისძვრები არ მოიძებნა."}, 404

        return events

    @event_ns.expect(event_model)
    @event_ns.doc(security='ApiKeyAuth', description='Create or update a seismic event (requires X-API-Key)')
    def post(self):
        """Create or update a seismic event (upsert, requires API key)"""
        # --- Auth check ---
        api_key = request.headers.get('X-API-Key')
        if api_key != Config.API_KEY:
            return {'error': 'Unauthorized - Invalid API key'}, 401

        # --- Parse request body ---
        args = event_parser.parse_args()

        # --- Convert origin_time to datetime ---
        try:
            origin_time = datetime.datetime.fromisoformat(args['origin_time'])
        except Exception:
            return {
                'error': 'Invalid origin_time format (use ISO 8601, e.g. 2025-10-24T12:20:00)'
            }, 400

        # --- Check if event already exists ---
        exist_event = SeismicEvent.query.filter_by(event_id=args['event_id']).first()
        if exist_event:
            # -------- UPDATE EXISTING EVENT --------
            exist_event.seiscomp_oid = args.get('seiscomp_oid')
            exist_event.origin_time = origin_time
            exist_event.origin_msec = args.get('origin_msec')
            exist_event.latitude = args['latitude']
            exist_event.longitude = args['longitude']
            exist_event.depth = args['depth']
            exist_event.region_ge = args.get('region_ge')
            exist_event.region_en = args.get('region_en')
            exist_event.area = args.get('area')
            exist_event.ml = args.get('ml')
            exist_event.shakemap_calculated = args.get('shakemap_calculated') or False

            exist_event.save()
            return {
                'message': f'Seismic event {exist_event.event_id} updated successfully'
            }, 200

        else:
            # -------- CREATE NEW EVENT --------
            new_event = SeismicEvent(
                event_id=args['event_id'],
                seiscomp_oid=args.get('seiscomp_oid'),
                origin_time=origin_time,
                origin_msec=args.get('origin_msec'),
                latitude=args['latitude'],
                longitude=args['longitude'],
                depth=args['depth'],
                region_ge=args.get('region_ge'),
                region_en=args.get('region_en'),
                area=args.get('area'),
                ml=args.get('ml'),
                shakemap_calculated=args.get('shakemap_calculated') or False
            )
            new_event.create()

            return {
                'message': f'Seismic event {new_event.event_id} created successfully'
            }, 201