import logging

from flask_restx import Resource
from flask import request
import datetime

from src.api.nsmodels import event_ns, event_model, event_parser
from src.utils import is_authorized_request
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
    @event_ns.doc(
        security=[{'ApiKeyAuth': []}, {'JsonWebToken': []}],
        description='Create or update a seismic event (requires X-API-Key or JWT Bearer token)',
    )
    def post(self):
        """Create or update a seismic event (upsert, API key or JWT)"""
        # --- ავტორიზაციის შემოწმება ---
        if not is_authorized_request():
            logger.warning("Event upsert denied: unauthorized")
            return {'error': 'არ გაქვს წვდომა. არ ხართ ავტორიზირებული.'}, 401

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
    @event_ns.expect(event_model)
    @event_ns.doc(
        security=[{'ApiKeyAuth': []}, {'JsonWebToken': []}],
        description='Update a seismic event by event_id (requires X-API-Key or JWT Bearer token)',
    )
    def put(self, event_id):
        """აახლებს მიწისძვრის მოვლენას event_id-ით."""
        if not is_authorized_request():
            logger.warning("Event update denied: event_id=%s unauthorized", event_id)
            return {'error': 'არ გაქვს წვდომა. არ ხართ ავტორიზირებული.'}, 401

        args = event_parser.parse_args()
        body_event_id = args.get("event_id")
        if body_event_id is not None and int(body_event_id) != int(event_id):
            return {'error': 'URL-ის event_id და body-ის event_id არ ემთხვევა.'}, 400

        event = SeismicEvent.query.filter_by(event_id=event_id).first()
        if not event:
            logger.info("Event update failed: event_id=%s not found", event_id)
            return {'error': f'მიწისძვრის მოვლენა ვერ მოიძებნა: {event_id}'}, 404

        try:
            origin_time = datetime.datetime.fromisoformat(args['origin_time'])
        except Exception:
            logger.info(
                "Event update failed: event_id=%s invalid origin_time format",
                event_id,
            )
            return {
                'error': 'origin_time ფორმატი არასწორია (გამოიყენე ISO 8601, მაგ.: 2025-10-24T12:20:00)'
            }, 400

        event.seiscomp_oid = args.get('seiscomp_oid')
        event.origin_time = origin_time
        event.origin_msec = args.get('origin_msec')
        event.latitude = args['latitude']
        event.longitude = args['longitude']
        event.depth = args['depth']
        event.region_ge = args.get('region_ge')
        event.region_en = args.get('region_en')
        event.area = args.get('area')
        event.ml = args.get('ml')
        event.save()

        logger.info("Event updated via PUT: event_id=%s", event_id)
        return {'message': f'მიწისძვრის მოვლენა წარმატებით განახლდა: {event_id}'}, 200

    @event_ns.doc(security='ApiKeyAuth', description='Delete a seismic event by event_id (requires X-API-Key)')
    def delete(self, event_id):
        """შლის მიწისძვრის მოვლენას event_id-ით (არსებული მომხმარებელი უნდა იყოს ავტორიზირებული)."""
        if not is_authorized_request():
            logger.warning("Event delete denied: event_id=%s unauthorized", event_id)
            return {'error': 'არ გაქვს წვდომა. არ ხართ ავტორიზირებული.'}, 401

        event = SeismicEvent.query.filter_by(event_id=event_id).first()
        if not event:
            logger.info("Event delete failed: event_id=%s not found", event_id)
            return {'error': f'მიწისძვრის მოვლენა ვერ მოიძებნა: {event_id}'}, 404

        event.delete()
        logger.info("Event deleted: event_id=%s", event_id)
        return {'message': f'მიწისძვრის მოვლენა წარმატებით წაიშალა: {event_id}'}, 200