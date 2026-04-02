from flask_restx import reqparse, inputs
from src.extensions import api


auth_ns = api.namespace('Auth', description='API endpoint for Authentification related operations', path='/api')

registration_parser = reqparse.RequestParser()
registration_parser.add_argument('name', type=str, required=True, help="Name example: Roma (1-20 characters)")
registration_parser.add_argument('lastname', type=str, required=True, help="LastName example: Grigalashvili (1-20 characters)")
registration_parser.add_argument('email', type=inputs.email(check=True), required=True, help="Email example: roma.grigalashvili@iliauni.edu.ge")
registration_parser.add_argument('password', type=str, required=True, help="Password example: Grigalash1")
registration_parser.add_argument('passwordRepeat', type=str, required=True, help='Repeat the password example: Grigalash1')
registration_parser.add_argument('role_name', type=str, required=False, default='User', help="Name of the role example: User")

# Auth parser
auth_parser = reqparse.RequestParser()
auth_parser.add_argument("email", required=True, type=str, help="Email example: roma.grigalashvili@iliauni.edu.ge")
auth_parser.add_argument("password", required=True, type=str, help="Password example: Grigalash1")