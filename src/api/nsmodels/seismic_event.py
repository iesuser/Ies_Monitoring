from flask_restx import reqparse, fields
from src.extensions import api

event_ns = api.namespace('Events', description='API endpoint for Seismic event operations', path='/api')

# RESTX model for Swagger
event_model = api.model('SeismicEvent', {
    'event_id': fields.Integer(required=True, description='Primary key / manually assigned ID'),
    'seiscomp_oid': fields.String(required=True,description='SeisComP OID'),
    'origin_time': fields.DateTime(required=True, description='Origin time of the event'),
    'origin_msec': fields.Integer(description='Milliseconds of origin time'),
    'latitude': fields.Float(required=True, description='Latitude of the event'),
    'longitude': fields.Float(required=True, description='Longitude of the event'),
    'depth': fields.Float(required=True, description='Depth in km'),
    'region_ge': fields.String(description='Region GE'),
    'region_en': fields.String(description='Region EN'),
    'area': fields.String(description='Area name'),
    'ml': fields.Float(required=True, description='Local Magnitude (ML)'),
    'created_at': fields.DateTime(description='Record creation timestamp (UTC)'),
    'shakemap_status': fields.String(
        description='ShakeMap status (pending/running/generated/failed)',
        enum=['pending', 'running', 'generated', 'failed'],
    )
})

# Request Parser
event_parser = reqparse.RequestParser()
event_parser.add_argument("event_id", type=int, required=True, help="Primary key / manually assigned ID is required")
event_parser.add_argument("seiscomp_oid", type=str, required=True, help="SeisComP OID (optional)")
event_parser.add_argument("origin_time", type=str, required=True, help="Origin time is required (ISO 8601)")
event_parser.add_argument("origin_msec", type=int, required=False, help="Milliseconds of origin time (optional)")
event_parser.add_argument("latitude", type=float, required=True, help="Latitude is required")
event_parser.add_argument("longitude", type=float, required=True, help="Longitude is required")
event_parser.add_argument("depth", type=float, required=True, help="Depth is required")
event_parser.add_argument("region_ge", type=str, required=False, help="Region GE (optional)")
event_parser.add_argument("region_en", type=str, required=False, help="Region EN (optional)")
event_parser.add_argument("area", type=str, required=False, help="Area (optional)")
event_parser.add_argument("ml", type=float, required=True, help="Local Magnitude (ML)")