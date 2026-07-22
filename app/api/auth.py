import logging
from datetime import datetime

from flask import current_app, jsonify
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    current_user,
    get_jwt_identity,
    jwt_required,
    set_refresh_cookies,
    unset_jwt_cookies,
)
from flask_restx import Resource

from app.api.nsmodels import auth_ns, auth_parser, registration_parser
from app.models import User
from app.utils import normalize_email, validate_password

logger = logging.getLogger("app.auth")


def _access_token_expires_in():
    expires = current_app.config.get("JWT_ACCESS_TOKEN_EXPIRES")
    if expires is None:
        return None
    return int(expires.total_seconds())


def _build_login_response(user):
    access_token = create_access_token(identity=user.uuid)
    refresh_token = create_refresh_token(identity=user.uuid)

    response = jsonify(
        {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": _access_token_expires_in(),
        }
    )
    set_refresh_cookies(response, refresh_token)
    return response


@auth_ns.route("/register")
@auth_ns.doc(
    responses={
        200: "OK",
        400: "Invalid Argument",
        401: "Unauthorized",
        403: "Forbidden",
    }
)
class RegistrationApi(Resource):
    @jwt_required()
    @auth_ns.doc(parser=registration_parser)
    @auth_ns.doc(security="JsonWebToken")
    def post(self):
        if not current_user.check_permission("can_users"):
            logger.warning(
                "Registration denied: actor_uuid=%s missing can_users",
                current_user.uuid,
            )
            return {"error": "forbidden", "message": "Missing required permission: can_users"}, 403

        args = registration_parser.parse_args()

        try:
            normalized_email = normalize_email(args["email"])
        except ValueError as err:
            logger.info("Registration failed: invalid email format")
            return {"error": "validation_error", "message": str(err)}, 400

        first_name = (args.get("first_name") or "").strip()
        last_name = (args.get("last_name") or "").strip()
        if not first_name or not last_name:
            return {
                "error": "validation_error",
                "message": "first_name and last_name are required.",
            }, 400

        if args["password"] != args["passwordRepeat"]:
            logger.info("Registration failed: email=%s password mismatch", normalized_email)
            return {"error": "validation_error", "message": "Passwords do not match."}, 400

        try:
            validate_password(args["password"])
        except ValueError as err:
            logger.info("Registration failed: email=%s password policy error", normalized_email)
            return {"error": "validation_error", "message": str(err)}, 400

        if User.query.filter_by(email=normalized_email).first():
            logger.info("Registration failed: email=%s already exists", normalized_email)
            return {
                "error": "conflict",
                "message": "Email address is already registered.",
            }, 400

        new_user = User(
            first_name=first_name,
            last_name=last_name,
            email=normalized_email,
            password=args["password"],
            created_by_user_id=current_user.id,
            updated_by_user_id=current_user.id,
        )
        new_user.create()
        logger.info("Registration success: email=%s actor_uuid=%s", normalized_email, current_user.uuid)

        return {"message": "User registered successfully.", "user": new_user.to_dict()}, 200


@auth_ns.route("/login")
class AuthorizationApi(Resource):
    @auth_ns.doc(parser=auth_parser)
    def post(self):
        try:
            args = auth_parser.parse_args()

            try:
                normalized_email = normalize_email(args["email"])
            except ValueError:
                return {"error": "invalid_credentials", "message": "Invalid email or password."}, 400

            user = User.query.filter_by(email=normalized_email).first()
            if not user or not user.check_password(args["password"]):
                return {"error": "invalid_credentials", "message": "Invalid email or password."}, 400

            if not user.is_active:
                logger.warning("Login denied: user_uuid=%s is inactive", user.uuid)
                return {"error": "forbidden", "message": "User account is inactive."}, 403

            user.last_login_at = datetime.now()
            user.save()

            return _build_login_response(user)
        except Exception:
            logger.exception("Login failed with unexpected error")
            return {"error": "internal_error", "message": "Internal error occurred during authorization."}, 500


@auth_ns.route("/refresh")
class AccessTokenRefreshApi(Resource):
    @jwt_required(refresh=True)
    def post(self):
        identity = get_jwt_identity()
        user = User.query.filter_by(uuid=identity).first()
        if not user:
            return {"error": "not_found", "message": "User not found."}, 404
        if not user.is_active:
            return {"error": "forbidden", "message": "User account is inactive."}, 403

        # Cookie rotation: issue a new refresh cookie alongside the new access token.
        # Full DB-backed revoke/replay protection lands with the refresh_tokens model.
        response = _build_login_response(user)
        return response


@auth_ns.route("/logout")
class LogoutApi(Resource):
    def post(self):
        response = jsonify({"message": "logout success"})
        unset_jwt_cookies(response)
        return response
