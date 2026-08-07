"""Shared helpers for API tests."""

from app.models import Permission, User, UserPermission

VALID_PASSWORD = "TestPass123!@#"
ADMIN_EMAIL = "admin@example.com"
USER_EMAIL = "user@example.com"

PERMISSIONS = (
    ("can_users", "Users Management", "Register and manage users."),
    ("can_permissions", "Permissions Management", "Manage and assign permissions."),
    ("can_recips", "Recips Management", "Manage notification recipients."),
    ("can_recips_read", "Recips Read-Only", "Read recipients list and details."),
    ("can_event_view", "Seismic Events View", "View seismic events, magnitudes, and beachballs."),
    ("can_event_edit", "Seismic Events Edit", "Create, update, and delete seismic events, magnitudes, and beachballs."),
)


def ensure_permission(code, name, description):
    permission = Permission.query.filter_by(code=code).first()
    if permission:
        return permission

    permission = Permission(
        code=code,
        name=name,
        description=description,
        is_active=True,
    )
    permission.create()
    return permission


def seed_permissions():
    return [ensure_permission(code, name, description) for code, name, description in PERMISSIONS]


def create_user(
    *,
    email,
    password=VALID_PASSWORD,
    first_name="Test",
    last_name="User",
    is_active=True,
    permission_codes=None,
):
    user = User(
        first_name=first_name,
        last_name=last_name,
        email=email,
        is_active=is_active,
    )
    user.password = password
    user.create()

    if permission_codes:
        for code in permission_codes:
            permission = Permission.query.filter_by(code=code).first()
            if not permission:
                continue
            assignment = UserPermission(
                user_id=user.id,
                permission_id=permission.id,
                granted_by_user_id=user.id,
            )
            assignment.create()

    return user


def auth_headers(access_token):
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def login(client, email, password=VALID_PASSWORD):
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    return response
