from flask_restx import reqparse, fields
from src.extensions import api

shakemap_ns = api.namespace('Calc ShakeMap', description='API endpoint for ShakeMap operations', path='/api')

shakemap_model = shakemap_ns.model("SeisCompEvent", {
    "seiscomp_oid": fields.String(required=True, description="SeisComP Event OID")
})


# Request Parser
shakemap_parser = reqparse.RequestParser()
shakemap_parser.add_argument("seiscomp_oid", type=str, required=True, help="SeisComP OID is required")