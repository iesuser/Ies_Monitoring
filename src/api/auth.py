import logging

from flask_restx import Resource
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, current_user

from src.models import User, Role
from src.api.nsmodels import auth_ns, registration_parser, auth_parser
from src.services import validate_password

logger = logging.getLogger("app.auth")


@auth_ns.route('/registration')
@auth_ns.doc(responses={200: 'OK', 400: 'Invalid Argument', 401: 'JWT Token Expires', 403: 'Forbidden', 404: 'Not Found'})
class RegistrationApi(Resource):
    @jwt_required()
    @auth_ns.doc(parser=registration_parser)
    @auth_ns.doc(security='JsonWebToken')
    def post(self):
        
        # ვამოწმებთ, აქვს თუ არა მიმდინარე მომხმარებელს ახალი ანგარიშის რეგისტრაციის უფლება.
        if not (current_user.check_permission('is_admin') or current_user.check_permission('can_users')):
            logger.warning("Registration denied: actor_uuid=%s missing permissions", current_user.uuid)
            return {"error": "არ გაქვს მომხმარებლის რეგისტრაციის ნებართვა."}, 403


        args = registration_parser.parse_args()

        # ვამოწმებთ, ემთხვევა თუ არა პაროლის წესებს და განმეორებით შეყვანას.
        if args["password"] != args["passwordRepeat"]:
            logger.info("Registration failed: email=%s password mismatch", args["email"])
            return {"error": "პაროლები არ ემთხვევა."}, 400

        try:
            validate_password(args["password"])
        except ValueError as err:
            logger.info("Registration failed: email=%s password policy error", args["email"])
            return {"error": str(err)}, 400

        if User.query.filter_by(email=args["email"]).first():
            logger.info("Registration failed: email=%s already exists", args["email"])
            return {"error": "ელ.ფოსტის მისამართი უკვე რეგისტრირებულია."}, 400

        role = Role.query.filter_by(name=args["role_name"]).first()
        if not role:
            logger.info("Registration failed: email=%s role not found=%s", args["email"], args["role_name"])
            return {"error": "როლი ვერ მოიძებნა."}, 400

        new_user = User(
            name=args["name"],
            lastname=args["lastname"],
            email=args["email"],
            password=args["password"],
            role_id=role.id
        )

        new_user.create()
        logger.info("Registration success: email=%s role=%s", args["email"], role.name)

        return {"message": "მომხმარებელი წარმატებით დარეგისტრირდა."}, 200
    
@auth_ns.route('/login')
@auth_ns.doc(responses={200: 'OK', 400: 'Invalid Argument', 401: 'JWT Token Expires', 403: 'Forbidden', 404: 'Not Found'})
class AuthorizationApi(Resource):
    @auth_ns.doc(parser=auth_parser)
    def post(self):
        args = auth_parser.parse_args()

        # მომხმარებელს ვეძებთ ელფოსტის მიხედვით.
        user = User.query.filter_by(email=args["email"]).first()
        if not user:
            logger.info("Login failed: email=%s user not found", args["email"])
            return {"error": "შეყვანილი პაროლი ან ელ.ფოსტა არასწორია."}, 400

        # ვამოწმებთ, ემთხვევა თუ არა პაროლი.
        if user.check_password(args["password"]):

            # ვქმნით ტოკენებს მომხმარებლის UUID იდენტობით.
            access_token = create_access_token(identity=user.uuid)
            refresh_token = create_refresh_token(identity=user.uuid)

            # ვიღებთ უფლებებს და ვქმნით permissions ტოკენს.
            permissions = user.role.get_permissions()

            permissions_token = create_access_token(identity={
                **permissions
            })

            logger.info("Login success: user_uuid=%s email=%s", user.uuid, user.email)

            return {
                "message": "წარმატებით გაიარეთ ავტორიზაცია.",
                "access_token": access_token,
                "refresh_token": refresh_token,
                "permissions_token": permissions_token
            }, 200
        
        # თუ პაროლი არასწორია, ვაბრუნებთ ავტორიზაციის შეცდომას.
        else:
            logger.info("Login failed: email=%s invalid password", args["email"])
            return {"error": "შეყვანილი პაროლი ან ელ.ფოსტა არასწორია."}, 400

@auth_ns.route('/refresh')
@auth_ns.doc(responses={200: 'OK', 400: 'Invalid Argument', 401: 'JWT Token Expires', 403: 'Forbidden', 404: 'Not Found'})
class AccessTokenRefreshApi(Resource):
    @jwt_required(refresh=True)
    @auth_ns.doc(security='JsonWebToken')
    def post(self):
        identity = get_jwt_identity()
        access_token = create_access_token(identity=identity)
        logger.info("Access token refresh success: identity=%s", identity)
        response = {
            "access_token": access_token
        }

        return response