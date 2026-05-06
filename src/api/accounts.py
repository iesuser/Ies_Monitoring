import logging

from flask_restx import Resource
from flask_jwt_extended import jwt_required, current_user, get_jwt_identity
from flask import request

from src.models import User, Role
from src.api.nsmodels import accounts_ns, user_model, user_parser, accounts_model, accounts_parser, roles_model, roles_parser, password_reset_parser, request_password_reset_parser, change_password_parser
from src.services import mail, url_serializer
from src.services import validate_password

from datetime import datetime, timedelta

logger = logging.getLogger("app.auth")


@accounts_ns.route('/user')
@accounts_ns.doc(responses={200: 'OK', 400: 'Invalid Argument', 401: 'JWT Token Expires', 403: 'Forbidden', 404: 'Not Found'})
class UserApi(Resource):
    @jwt_required()
    @accounts_ns.doc(security='JsonWebToken')
    @accounts_ns.marshal_with(user_model)
    def get(self):
        """საკუთარი მომხმარებლის მონაცემების მიღება"""
        identity = get_jwt_identity()
        user = User.query.filter_by(uuid=identity).first()

        if user:
            role = Role.query.filter_by(id=user.role_id).first()
            if not role:
                logger.info("Get user failed: uuid=%s role not found", identity)
                return {"error": "როლი ვერ მოიძებნა."}, 400
            user.role_name = role.name
            logger.info("Get user success: uuid=%s", identity)
            return user, 200
        else:
            logger.info("Get user failed: uuid=%s not found", identity)
            return {'error': 'მომხმარებელი ვერ მოიძებნა.'}, 404

@accounts_ns.route('/user/<string:uuid>')
@accounts_ns.doc(responses={200: 'OK', 400: 'Invalid Argument', 401: 'JWT Token Expires', 403: 'Forbidden', 404: 'Not Found'})
class UserUpdateAPI(Resource):
    @jwt_required()
    @accounts_ns.doc(security='JsonWebToken')
    @accounts_ns.expect(user_parser)
    def put(self, uuid):
        """შესაძლებელია საკუთარი მონაცემის განახლება"""
        identity = get_jwt_identity()

        if identity == uuid:
            user = User.query.filter_by(uuid=uuid).first()

            if not user:
                logger.info("Update profile failed: uuid=%s not found", uuid)
                return {'error': 'მომხმარებელი ვერ მოიძებნა.'}, 404

            args = user_parser.parse_args()
               
            # მომხმარებლის ველების განახლება
            user.name = args["name"]
            user.lastname = args["lastname"]
            
            # ცვლილებების შენახვა
            user.save()
            logger.info("Update profile success: uuid=%s", uuid)

            return {'message': 'მონაცემები წარმატებით განახლდა.'}, 200
        else:
            logger.warning(
                "Update profile denied: actor_uuid=%s target_uuid=%s",
                identity,
                uuid,
            )
            return {'error': "არ გაქვს მონაცემების განახლების ნებართვა."}, 403

@accounts_ns.route('/accounts')
@accounts_ns.doc(responses={200: 'OK', 400: 'Invalid Argument', 401: 'JWT Token Expires', 403: 'Forbidden', 404: 'Not Found'})
class AccountsListApi(Resource):
    @jwt_required()
    @accounts_ns.doc(security='JsonWebToken')
    @accounts_ns.marshal_with(accounts_model)
    def get(self):
        """მომხმარებლების სიის მიღება, წვდომა აქვს მხოლოდ role-ით (can_users) """
        # ვამოწმებთ, აქვს თუ არა მომხმარებელს შესაბამისი უფლება
        if not current_user.check_permission('can_users'):
            logger.warning("List accounts denied: actor_uuid=%s", current_user.uuid)
            return {"error": "არ გაქვს მომხმარებლის ნახვის ნებართვა."}, 403

        # ბაზიდან ყველა მომხმარებლის წამოღება
        users = User.query.all()
        # response-ის მონაცემების მომზადება list comprehension-ით
        result = [
            {
                "uuid": user.uuid,
                "username": f"{user.name} {user.lastname}",
                "email": user.email,
                "role": {
                    "id": user.role.id if user.role else "null",
                    "name": user.role.name if user.role else "No Role",
                    "is_admin": user.role.is_admin if user.role else False,
                    "can_users": user.role.can_users if user.role else False,
                    "can_shakemap": user.role.can_shakemap if user.role else False,
                    "can_events": user.role.can_events if user.role else False,
                } if user.role else None,
            }
            for user in users
        ]

        logger.info("List accounts success: count=%s actor_uuid=%s", len(result), current_user.uuid)
        return result, 200
@accounts_ns.route('/accounts/<string:uuid>')
@accounts_ns.doc(responses={200: 'OK', 400: 'Invalid Argument', 401: 'JWT Token Expires', 403: 'Forbidden', 404: 'Not Found'})
class AccountsApi(Resource):
    @jwt_required()
    @accounts_ns.doc(security='JsonWebToken')
    @accounts_ns.doc(parser=accounts_parser)
    def put(self, uuid):
        """მომხმარებლის როლის შეცვლა, წვდომა აქვს მხოლოდ role-ით (can_users)"""
        # ვამოწმებთ, აქვს თუ არა მომხმარებელს შესაბამისი უფლება
        if not current_user.check_permission('can_users'):
            logger.warning("Update account role denied: actor_uuid=%s", current_user.uuid)
            return {"error": "არ გაქვს მომხმარებლის ნახვის ნებართვა."}, 403

        args = accounts_parser.parse_args()
        role_id = args["role_id"]

        user = User.query.filter_by(uuid=uuid).first()
        if not user:
            logger.info("Update account role failed: target_uuid=%s not found", uuid)
            return {"error": "მომხმარებელი არ მოიძებნა"}, 404
            
        role = Role.query.get(role_id)
        if not role:
            logger.info("Update account role failed: role_id=%s not found", role_id)
            return {"error": "როლი არ მოიძებნა"}, 404
        
        user.role_id = role_id
        user.save()
        logger.info(
            "Update account role success: actor_uuid=%s target_uuid=%s role_id=%s",
            current_user.uuid,
            uuid,
            role_id,
        )
        return {"message": "მომხმარებლის როლი წარმატებით განახლდა"}, 200

@accounts_ns.route('/roles')
@accounts_ns.doc(responses={200: 'OK', 400: 'Invalid Argument', 401: 'JWT Token Expires', 403: 'Forbidden', 404: 'Not Found'})
class RolesListApi(Resource):
    @jwt_required()
    @accounts_ns.doc(security='JsonWebToken')
    @accounts_ns.marshal_with(roles_model)
    def get(self):
        """როლების სიის მიღება, წვდომა აქვს მხოლოდ role-ით (can_users)"""
        # ვამოწმებთ, აქვს თუ არა მომხმარებელს შესაბამისი უფლება
        if not current_user.check_permission('can_users'):
            logger.warning("List roles denied: actor_uuid=%s", current_user.uuid)
            return {"error": "არ გაქვს მომხმარებლის ნახვის ნებართვა."}, 403
        
        # ბაზიდან ყველა როლის წამოღება
        roles = Role.query.all()
        
        if not roles:
            logger.info("List roles: no roles found")
            return {'error': 'როლი ვერ მოიძებნა.'}, 404
        
        logger.info("List roles success: count=%s actor_uuid=%s", len(roles), current_user.uuid)
        return roles, 200
    
    @jwt_required()
    @accounts_ns.doc(security='JsonWebToken')
    @accounts_ns.doc(parser=roles_parser)
    def post(self):
        """როლის დამატება, წვდომა აქვს მხოლოდ role-ით (can_users)"""
        # ვამოწმებთ, აქვს თუ არა მომხმარებელს შესაბამისი უფლება
        if not current_user.check_permission('can_users'):
            logger.warning("Create role denied: actor_uuid=%s", current_user.uuid)
            return {"error": "არ გაქვს მომხმარებლის განახლების ნებართვა."}, 403
        
        # შემოსული არგუმენტების დამუშავება
        args = roles_parser.parse_args()
        
        # ვამოწმებთ, ხომ არ არსებობს უკვე იგივე როლი
        if Role.query.filter_by(name=args['name']).first():
            logger.info("Create role failed: role=%s already exists", args["name"])
            return {"error": "ეს როლი უკვე არსებობს."}, 400
        
        # ახალი როლის შექმნა
        new_role = Role(
            name=args['name'],
            is_admin=args.get('is_admin', False),
            can_users=args.get('can_users', False),
            can_shakemap=args.get('can_shakemap', False),
            can_events=args.get('can_events', False),
        )
        
        # ახალი როლის ბაზაში შენახვა
        new_role.create()
        logger.info("Create role success: role_id=%s role=%s", new_role.id, new_role.name)
        return {"message": f"როლი წარმატებით დაემატა."}, 200

@accounts_ns.route('/roles/<int:role_id>')
@accounts_ns.doc(responses={200: 'OK', 400: 'Invalid Argument', 401: 'JWT Token Expires', 403: 'Forbidden', 404: 'Not Found'})
class RolesAPI(Resource):
    @jwt_required()
    @accounts_ns.doc(security='JsonWebToken')
    @accounts_ns.marshal_with(roles_model)
    def get(self, role_id):
        """როლის დეტალების მიღება, წვდომა აქვს მხოლოდ role-ით (can_users)"""
        # ვამოწმებთ, აქვს თუ არა მომხმარებელს შესაბამისი უფლება
        if not current_user.check_permission('can_users'):
            logger.warning("Get role denied: actor_uuid=%s role_id=%s", current_user.uuid, role_id)
            return {"error": "არ გაქვს მომხმარებლის ნახვის ნებართვა."}, 403
        
        # role_id-ით როლის წამოღება
        role = Role.query.get(role_id)
        
        if not role:
            logger.info("Get role failed: role_id=%s not found", role_id)
            return {'error': 'როლი ვერ მოიძებნა.'}, 404
        
        logger.info("Get role success: role_id=%s", role_id)
        return role, 200

    @jwt_required()
    @accounts_ns.doc(security = 'JsonWebToken')
    @accounts_ns.doc(parser=roles_parser)
    def put(self, role_id):
        """როლის განახლება, წვდომა აქვს მხოლოდ role-ით (can_users)"""
        # ვამოწმებთ, აქვს თუ არა მომხმარებელს შესაბამისი უფლება
        if not current_user.check_permission('can_users'):
            logger.warning("Update role denied: actor_uuid=%s role_id=%s", current_user.uuid, role_id)
            return {"error": "არ გაქვს მომხმარებლის განახლების ნებართვა."}, 403

        args = roles_parser.parse_args()
        # როლის მოძიება ID-ით (და არა სახელით)
        role = Role.query.get(role_id)

        if not role:
            logger.info("Update role failed: role_id=%s not found", role_id)
            return {"error": "როლი ვერ მოიძებნა."}, 404

        # გადმოცემული ველების მიხედვით როლის განახლება
        if args['name'] is not None:
            role.name = args['name']
        if args['is_admin'] is not None:
            role.is_admin = args['is_admin']
        if args['can_users'] is not None:
            role.can_users = args['can_users']
        if args['can_shakemap'] is not None:
            role.can_shakemap = args['can_shakemap']
        if args['can_events'] is not None:
            role.can_events = args['can_events']
        role.save()
        logger.info("Update role success: role_id=%s", role_id)
        return {"message": f"როლი წარმატებით განახლდა."}, 200
    
@accounts_ns.route('/request_reset_password')
@accounts_ns.doc(responses={200: 'OK', 400: 'Invalid Argument', 401: 'JWT Token Expires', 403: 'Forbidden', 404: 'Not Found'})
class RequestResetPassword(Resource):
    @accounts_ns.doc(parser=request_password_reset_parser)
    def post(self):
        ''' პაროლის შეცვლის მოთხოვნის გაგზავნა '''
        args = request_password_reset_parser.parse_args()
        email = args.get('modalEmail')

        user = User.query.filter_by(email=email).first()

        if not user:
            logger.info("Reset request failed: email=%s user not found", email)
            return {'error' : 'მითითებული ელ.ფოსტით მომხმარებელი არ არსებობს'}, 400
        
        token = url_serializer.generate_token(data=user.uuid, salt='reset_password')
        reset_url = f'{request.url_root}reset_password/{token}'

        subject = 'პაროლის შეცვლა'
        message = f'მოგესალმებით,\nპაროლის შესაცვლელად გთხოვთ გადახვიდეთ ლინკზე: {reset_url}'
        
        last_sent = user.last_sent_email
        current_time = datetime.now()
        difference = current_time - last_sent
        if difference < timedelta(seconds=60):
            logger.info("Reset request throttled: user_uuid=%s", user.uuid)
            return {'error': f'გთხოვთ თავიდან სცადოთ {int(60 - difference.total_seconds())} წამში'}, 400

        try:
            status = mail.send_mail(emails=[email], subject=subject, message=message)

            if not status:
                logger.error("Reset request email send failed: user_uuid=%s", user.uuid)
                return{'error': 'ელ.ფოსტის გაგზავნის დროს დაფიქსირდა შეცდომა'}, 400
            
            current_time = datetime.now()

            user.last_sent_email = current_time
            user.save()
            logger.info("Reset request success: user_uuid=%s", user.uuid)

            return {'message': 'გთხოვთ შეამოწმოთ ელ.ფოსტა, ვერიფიკაციის ლინკი გამოგზავნილია'}, 200
        except Exception as err:
            logger.exception("Reset request exception: email=%s", email)
            return {'error': f'ელ.ფოსტის გაგზავნის დროს დაფიქსირდა შეცდომა: {err}'}, 400
        
@accounts_ns.route('/reset_password')
@accounts_ns.doc(responses={200: 'OK', 400: 'Invalid Argument', 401: 'JWT Token Expires', 403: 'Forbidden', 404: 'Not Found'})
class ResetPassword(Resource):
    @accounts_ns.doc(parser=password_reset_parser)
    def put(self):
        ''' პაროლის შეცვლა '''
        args = password_reset_parser.parse_args()

        token = args.get('token')
        uuid = url_serializer.unload_token(token=token,salt='reset_password', max_age_seconds=300)

        if uuid == 'invalid':
            logger.info("Reset password failed: invalid token")
            return {'error': 'არასწორი ტოკენი'}, 400
        elif uuid == 'expired':
            logger.info("Reset password failed: expired token")
            return {'error': 'არსებულ ტოკენს გაუვიდა ვადა'}, 400
        
        user = User.query.filter_by(uuid=uuid).first()
        if not user:
            logger.info("Reset password failed: token user missing uuid=%s", uuid)
            return {'error': 'მომხმარებელი ვერ მოიძებნა'}, 404
        
        if args.get('password') != args.get("retype_password"):
            logger.info("Reset password failed: user_uuid=%s password mismatch", user.uuid)
            return {"error": "პაროლები არ ემთხვევა."}, 400

        try:
            validate_password(args.get("password"))
        except ValueError as err:
            logger.info("Reset password failed: user_uuid=%s password policy error", user.uuid)
            return {"error": str(err)}, 400


        password = args.get('password')
        try:
            user.password = password
            user.save()
            logger.info("Reset password success: user_uuid=%s", user.uuid)
            return {'message': 'პაროლი წარმატებით დარედაქტირდა'}, 200
        except Exception:
            logger.exception("Reset password exception: user_uuid=%s", user.uuid)
            return {'error': 'პაროლის შეცვლის დროს დაფიქსირდა შეცდომა'}, 400


@accounts_ns.route('/change_password')
@accounts_ns.doc(responses={200: 'OK', 400: 'Invalid Argument', 401: 'JWT Token Expires', 403: 'Forbidden', 404: 'Not Found'})
class ChangePassword(Resource):
    @jwt_required()
    @accounts_ns.doc(security='JsonWebToken')
    @accounts_ns.doc(parser=change_password_parser)
    def put(self):
        """ავტორიზებული მომხმარებლის პაროლის შეცვლა (მეილის გარეშე)."""
        args = change_password_parser.parse_args()
        identity = get_jwt_identity()
        user = User.query.filter_by(uuid=identity).first()

        if not user:
            logger.info("Change password failed: user not found uuid=%s", identity)
            return {'error': 'მომხმარებელი ვერ მოიძებნა'}, 404

        if args.get('password') != args.get("retype_password"):
            logger.info("Change password failed: user_uuid=%s password mismatch", user.uuid)
            return {"error": "პაროლები არ ემთხვევა."}, 400

        try:
            validate_password(args.get("password"))
        except ValueError as err:
            logger.info("Change password failed: user_uuid=%s password policy error", user.uuid)
            return {"error": str(err)}, 400

        if not user.check_password(args.get("current_password")):
            logger.info("Change password failed: user_uuid=%s wrong current password", user.uuid)
            return {"error": "ძველი პაროლი არასწორია."}, 400

        try:
            user.password = args.get('password')
            user.save()
            logger.info("Change password success: user_uuid=%s", user.uuid)
            return {'message': 'პაროლი წარმატებით შეიცვალა'}, 200
        except Exception:
            logger.exception("Change password exception: user_uuid=%s", user.uuid)
            return {'error': 'პაროლის შეცვლის დროს დაფიქსირდა შეცდომა'}, 400