from flask import request
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from app.config import Config
from app.extensions import db
from app.models import User


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


def has_user_permission(user, permission_code):
    """ამოწმებს აქვს თუ არა კონკრეტულ მომხმარებელს აქტიური უფლება."""
    if not user or not getattr(user, "is_active", False):
        return False

    from app.models.permissions import Permission
    from app.models.user_permissions import UserPermission

    assignment = (
        db.session.query(UserPermission.id)
        .join(Permission, Permission.id == UserPermission.permission_id)
        .filter(
            UserPermission.user_id == user.id,
            UserPermission.degranted_at.is_(None),
            Permission.is_active.is_(True),
            Permission.code == permission_code,
        )
        .first()
    )
    return assignment is not None


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

        return has_user_permission(user, permission)
    except Exception:
        return False