import pytest

from app import create_app
from app.config import TestingConfig
from app.extensions import db
from tests.helpers import (
    ADMIN_EMAIL,
    USER_EMAIL,
    VALID_PASSWORD,
    auth_headers,
    create_user,
    login,
    seed_permissions,
)


@pytest.fixture()
def app():
    application = create_app(TestingConfig)

    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def permissions(app):
    return seed_permissions()


@pytest.fixture()
def admin_user(app, permissions):
    return create_user(
        email=ADMIN_EMAIL,
        first_name="Admin",
        last_name="User",
        password=VALID_PASSWORD,
        permission_codes=["can_users", "can_permissions", "can_recips", "can_event_view", "can_event_edit"],
    )


@pytest.fixture()
def plain_user(app, permissions):
    return create_user(
        email=USER_EMAIL,
        first_name="Plain",
        last_name="User",
        password=VALID_PASSWORD,
        permission_codes=[],
    )


@pytest.fixture()
def admin_token(client, admin_user):
    response = login(client, ADMIN_EMAIL, VALID_PASSWORD)
    assert response.status_code == 200
    return response.get_json()["access_token"]


@pytest.fixture()
def user_token(client, plain_user):
    response = login(client, USER_EMAIL, VALID_PASSWORD)
    assert response.status_code == 200
    return response.get_json()["access_token"]


@pytest.fixture()
def admin_auth_headers(admin_token):
    return auth_headers(admin_token)


@pytest.fixture()
def user_auth_headers(user_token):
    return auth_headers(user_token)
