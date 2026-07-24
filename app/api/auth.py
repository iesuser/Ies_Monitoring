import logging
from datetime import datetime

from flask import current_app, jsonify
from flask_jwt_extended import (
    current_user,
    get_jwt,
    get_jwt_identity,
    jwt_required,
    set_refresh_cookies,
    unset_jwt_cookies,
    verify_jwt_in_request,
)
from flask_restx import Resource

from app.api.nsmodels import auth_ns, auth_parser, registration_parser
from app.models import User
from app.utils import normalize_email, validate_password
from app.utils.refresh_tokens import (
    RefreshTokenError,
    find_by_jti,
    get_raw_refresh_token_from_request,
    issue_token_pair,
    revoke_all_user_tokens,
    revoke_token,
    rotate_refresh_token,
)

logger = logging.getLogger("app.auth")


def _access_token_expires_in():
    expires = current_app.config.get("JWT_ACCESS_TOKEN_EXPIRES")
    if expires is None:
        return None
    return int(expires.total_seconds())


def _auth_response(access_token, refresh_token):
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

            access_token, refresh_token, _ = issue_token_pair(user)
            return _auth_response(access_token, refresh_token)
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

        claims = get_jwt()
        jti = claims.get("jti")
        raw_refresh = get_raw_refresh_token_from_request()
        if not jti or not raw_refresh:
            return {"error": "token_revoked", "message": "Refresh token is missing."}, 401

        try:
            access_token, refresh_token, _ = rotate_refresh_token(
                user,
                jti=jti,
                raw_refresh_token=raw_refresh,
            )
        except RefreshTokenError as err:
            response = jsonify({"error": err.code, "message": err.message})
            unset_jwt_cookies(response)
            return response, err.status_code

        return _auth_response(access_token, refresh_token)


@auth_ns.route("/logout")
class LogoutApi(Resource):
    def post(self):
        """Revoke the current refresh session (docs/05) and clear cookies."""
        try:
            verify_jwt_in_request(refresh=True)
            jti = get_jwt().get("jti")
            record = find_by_jti(jti) if jti else None
            if record and record.revoked_at is None:
                revoke_token(record)
                logger.info("Logout revoked refresh token: jti=%s user_id=%s", record.jti, record.user_id)
        except Exception:
            # Idempotent logout: missing/invalid refresh cookie still clears cookies.
            logger.info("Logout without valid refresh cookie")

        response = jsonify({"message": "logout success"})
        unset_jwt_cookies(response)
        return response


@auth_ns.route("/logout_all")
class LogoutAllApi(Resource):
    @jwt_required()
    @auth_ns.doc(security="JsonWebToken")
    def post(self):
        """Revoke every active refresh session for the current user."""
        count = revoke_all_user_tokens(current_user.id)
        logger.info("Logout-all revoked %s refresh tokens for user_uuid=%s", count, current_user.uuid)

        response = jsonify(
            {
                "message": "logout_all success",
                "revoked_sessions": count,
            }
        )
        unset_jwt_cookies(response)
        return response
