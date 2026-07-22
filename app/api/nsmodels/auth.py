from flask_restx import reqparse, inputs
from app.extensions import api


auth_ns = api.namespace(
    "Auth",
    description="API endpoints for authentication related operations",
    path="/auth",
)

registration_parser = reqparse.RequestParser()
registration_parser.add_argument(
    "first_name",
    type=str,
    required=True,
    help="First name example: Roma",
)
registration_parser.add_argument(
    "last_name",
    type=str,
    required=True,
    help="Last name example: Grigalashvili",
)
registration_parser.add_argument(
    "email",
    type=inputs.email(check=True),
    required=True,
    help="Email example: roma.grigalashvili@iliauni.edu.ge",
)
registration_parser.add_argument(
    "password",
    type=str,
    required=True,
    help="Password must be at least 12 characters with upper, lower, digit and special character",
)
registration_parser.add_argument(
    "passwordRepeat",
    type=str,
    required=True,
    help="Repeat the password",
)

auth_parser = reqparse.RequestParser()
auth_parser.add_argument(
    "email",
    required=True,
    type=str,
    help="Email example: roma.grigalashvili@iliauni.edu.ge",
)
auth_parser.add_argument(
    "password",
    required=True,
    type=str,
    help="Password",
)
