from flask import request
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from src.config import Config


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
