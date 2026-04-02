from flask_restx import reqparse, fields, inputs
from src.extensions import api


accounts_ns = api.namespace('Accounts', description='API endpoint for Role Management', path='/api')

user_model = accounts_ns.model('User', {
    'uuid': fields.String(required=True, type=str, description='The unique UUID of the user'),
    'name': fields.String(required=True, type=str, description='The name of the user'),
    'lastname': fields.String(required=True,  type=str, description='The lastname of the user'),
    'email': fields.String(required=True, type=inputs.email(check=True), description='The email of the user'),
    'role_name': fields.String(required=True, type=str, description='The role ID associated with the user')
})

# Auth parser
user_parser = reqparse.RequestParser()

user_parser.add_argument('name', required=True, type=str, help='Name example: Roma (1-20 characters)')
user_parser.add_argument('lastname', required=True, type=str, help='LastName example: Grigalashvili (1-20 characters)')


# Role model for documentation in Swagger UI
roles_model = accounts_ns.model('Roles', {
    'id': fields.Integer(readOnly=True, description='The unique identifier of a roles record'),
    'name': fields.String(required=True, description='Role Name'),
    'is_admin': fields.Boolean(description='Admin Privileges'),
    'can_users': fields.Boolean(description='Permission to manage users'),
    'can_shakemap': fields.Boolean(description='Permission to manage Shakemap'),
})


# Parser for Roles
roles_parser = reqparse.RequestParser()
roles_parser.add_argument('name', type=str, required=False, help='Role name')
roles_parser.add_argument('is_admin', type=inputs.boolean, required=False, help='Admin Privileges')
roles_parser.add_argument('can_users', type=inputs.boolean, required=False, help='Manage Users')
roles_parser.add_argument('can_shakemap', type=inputs.boolean, required=False, help='Manage Shakemap')

accounts_model = api.model('Accounts', {
        'uuid': fields.String(description='The unique UUID of the user'),
        "username": fields.String(description="Full Name (name + lastname)"),
        "email": fields.String(description="User Email"),
        "role": fields.Nested(roles_model, description="Role Details"),
})

accounts_parser = reqparse.RequestParser()
accounts_parser.add_argument('role_id', required=True, type=int, help='The unique identifier of a roles record')

request_password_reset_parser = reqparse.RequestParser()
request_password_reset_parser.add_argument("modalEmail", required=True, type=str, help="გთხოვთ შეიყვანეთ ახალი ელ.ფოსტა", default='satesto@example.com')

password_reset_parser = reqparse.RequestParser()
password_reset_parser.add_argument("token", required=True, type=str, help="გთხოვთ შეიყვანოთ ტოკენი", default='RmYTkyNTQxZjljMSI.Z8bhDw.1YCel4ik_BUzPqPpMZDvP8TaPMM.....')
password_reset_parser.add_argument("password", required=True, type=str, help="გთხოვთ შეიყვანეთ ახალი პაროლი", default='PAROLIparoli123')
password_reset_parser.add_argument("retype_password", required=True, type=str, help="გთხოვთ გაიმეოროთ პაროლი", default='PAROLIparoli123')

change_password_parser = reqparse.RequestParser()
change_password_parser.add_argument("current_password", required=True, type=str, help="გთხოვთ შეიყვანეთ ძველი პაროლი", default='PAROLIparoli123')
change_password_parser.add_argument("password", required=True, type=str, help="გთხოვთ შეიყვანეთ ახალი პაროლი", default='PAROLIparoli123')
change_password_parser.add_argument("retype_password", required=True, type=str, help="გთხოვთ გაიმეოროთ პაროლი", default='PAROLIparoli123')