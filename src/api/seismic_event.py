import logging

from flask_restx import Resource
from flask import request
import datetime

from src.api.nsmodels import event_ns, event_model, event_parser
from src.models import SeismicEvent
from src.config import Config

logger = logging.getLogger("app.events")

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
    @event_ns.marshal_list_with(event_model)  # Swagger-ში სქემის საჩვენებლად
    def get(self):
        """აბრუნებს მიწისძვრების სრულ სიას."""
        events = SeismicEvent.query.all()
        if not events:
            logger.info("Events list: no records found")
            return {"error": "მიწისძვრები არ მოიძებნა."}, 404

        logger.info("Events list success: count=%s", len(events))
        return events

    @event_ns.expect(event_model)
    @event_ns.doc(security='ApiKeyAuth', description='Create or update a seismic event (requires X-API-Key)')
    def post(self):
        """Create or update a seismic event (upsert, requires API key)"""
        # --- ავტორიზაციის შემოწმება ---
        api_key = request.headers.get('X-API-Key')
        if api_key != Config.API_KEY:
            logger.warning("Event upsert denied: invalid API key")
            return {'error': 'არ გაქვს წვდომა - API გასაღები არასწორია'}, 401

        # --- მოთხოვნის body-ის დამუშავება ---
        args = event_parser.parse_args()

        # --- origin_time-ის datetime-ად გარდაქმნა ---
        try:
            origin_time = datetime.datetime.fromisoformat(args['origin_time'])
        except Exception:
            logger.info(
                "Event upsert failed: event_id=%s invalid origin_time format",
                args.get("event_id"),
            )
            return {
                'error': 'origin_time ფორმატი არასწორია (გამოიყენე ISO 8601, მაგ.: 2025-10-24T12:20:00)'
            }, 400

        # --- ვამოწმებთ, არსებობს თუ არა უკვე ეს მოვლენა ---
        exist_event = SeismicEvent.query.filter_by(event_id=args['event_id']).first()
        if exist_event:
            # -------- არსებული მოვლენის განახლება --------
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

            exist_event.save()
            logger.info("Event updated: event_id=%s", exist_event.event_id)
            return {
                'message': f'მიწისძვრის მოვლენა წარმატებით განახლდა: {exist_event.event_id}'
            }, 200

        else:
            # -------- ახალი მოვლენის შექმნა --------
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
            )
            new_event.create()
            logger.info("Event created: event_id=%s", new_event.event_id)

            return {
                'message': f'მიწისძვრის მოვლენა წარმატებით დაემატა: {new_event.event_id}'
            }, 201


@event_ns.route('/events/<int:event_id>')
@event_ns.doc(
    responses={
        200: 'OK',
        401: 'Unauthorized',
        404: 'Not Found'
    }
)
class SeismicEventAPI(Resource):
    @event_ns.doc(security='ApiKeyAuth', description='Delete a seismic event by event_id (requires X-API-Key)')
    def delete(self, event_id):
        """შლის მიწისძვრის მოვლენას event_id-ით (საჭიროა API key)."""
        api_key = request.headers.get('X-API-Key')
        if api_key != Config.API_KEY:
            logger.warning("Event delete denied: event_id=%s invalid API key", event_id)
            return {'error': 'არ გაქვს წვდომა - API გასაღები არასწორია'}, 401

        event = SeismicEvent.query.filter_by(event_id=event_id).first()
        if not event:
            logger.info("Event delete failed: event_id=%s not found", event_id)
            return {'error': f'მიწისძვრის მოვლენა ვერ მოიძებნა: {event_id}'}, 404

        event.delete()
        logger.info("Event deleted: event_id=%s", event_id)
        return {'message': f'მიწისძვრის მოვლენა წარმატებით წაიშალა: {event_id}'}, 200