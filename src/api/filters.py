from flask_restx import Resource
from datetime import datetime
from flask_jwt_extended import jwt_required
from sqlalchemy import and_

from src.api.nsmodels import filter_ns, filter_parser, filter_model
from src.models import SeismicEvent


@filter_ns.route('/filter_event')
@filter_ns.doc(responses={200: 'OK', 400: 'Invalid Argument', 401: 'JWT Token Expires', 403: 'Unauthorized', 404: 'Not Found'})
class FilterEventAPI(Resource):
    @jwt_required()
    @filter_ns.doc(parser=filter_parser)
    @filter_ns.doc(security='JsonWebToken')
    @filter_ns.marshal_list_with(filter_model)
    def post(self):
        '''გავფილტროთ მიწისძვრები სხვადასხვა პარამეტრებით'''
        # Parse the filter arguments
        args = filter_parser.parse_args()

        # Extract filter parameters
        event_id = args.get("event_id")
        seiscomp_oid = args.get("seiscomp_oid")
        region = args.get("region")
        area = args.get("area")
        ml_min = args.get("ml_min")
        ml_max = args.get("ml_max")
        depth_min = args.get("depth_min")
        depth_max = args.get("depth_max")
        start_time = args.get("start_time")
        end_time = args.get("end_time")

        event_query = SeismicEvent.query

        # Apply event ID filter if provided
        if event_id:
            event_query = event_query.filter(SeismicEvent.event_id == event_id)
        
        # Apply seiscomp OID filter if provided
        if seiscomp_oid:
            event_query = event_query.filter(SeismicEvent.seiscomp_oid.like(f"%{seiscomp_oid}%"))

        # Apply region filter if provided
        if region:
            event_query = event_query.filter(SeismicEvent.region_ge.like(f"%{region}%"))

        # Apply origin time range filter only if both start_time and end_time are provided
        if start_time and not end_time:
            event_query = event_query.filter(SeismicEvent.origin_time >= start_time)
        elif end_time and not start_time:
            event_query = event_query.filter(SeismicEvent.origin_time <= end_time)
        elif start_time and end_time:
            event_query = event_query.filter(
                and_(
                    SeismicEvent.origin_time >= start_time,
                    SeismicEvent.origin_time <= end_time
                )
            )

        # Apply area filter if provided
        if area:
            event_query = event_query.filter(SeismicEvent.area == area)

        # Apply depth range filter if provided
        if depth_min and depth_max:
            event_query = event_query.filter(
                SeismicEvent.depth.between(depth_min, depth_max)
            )
        elif depth_min:
            event_query = event_query.filter(SeismicEvent.depth >= depth_min)
        elif depth_max:
            event_query = event_query.filter(SeismicEvent.depth <= depth_max)

        # Apply ML range filter if provided
        if ml_min and ml_max:
            event_query = event_query.filter(
                SeismicEvent.ml.between(ml_min, ml_max)
            )
        elif ml_min:
            event_query = event_query.filter(SeismicEvent.ml >= ml_min)
        elif ml_max:
            event_query = event_query.filter(SeismicEvent.ml <= ml_max)

        # Get the filtered events
        filtered_events = event_query.all()

        # Add calculated fields to each event
        for event in filtered_events:
            event.shakemap_calculated = True if event.shakemap_calculated else False

        # Return the filtered events
        return filtered_events, 200