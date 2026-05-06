from flask import request
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from src.config import Config
from src.models import User


def is_authorized_request():
    """ამოწმებს მოთხოვნას: X-API-Key ან JWT Bearer ტოკენი."""
    api_key = request.headers.get("X-API-Key")
    if api_key and api_key == Config.API_KEY:
        return True

    try:
        verify_jwt_in_request()
        identity = get_jwt_identity()
        return bool(identity)
    except Exception:
        return False

def have_permission(permission):
    """ამოწმებს მომხმარებლის უფლებას."""
    api_key = request.headers.get("X-API-Key")
    if api_key and api_key == Config.API_KEY:
        return True

    try:
        verify_jwt_in_request()
        identity = get_jwt_identity()
        user = User.query.filter_by(uuid=identity).first()
        if not user:
            return False

        if user.check_permission(permission):
            return True

        return False, {"error": "არ გაქვს უფლება (can_events)."}, 403
    except Exception:
        return False