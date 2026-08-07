from tests.helpers import USER_EMAIL, VALID_PASSWORD, auth_headers, create_user, login


def test_get_current_user(client, admin_auth_headers, admin_user):
    response = client.get("/api/accounts/ourself", headers=admin_auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data["email"] == admin_user.email
    assert data["can_users"] is True
    assert data["can_permissions"] is True
    assert data["can_recips"] is True
    assert data["can_event_view"] is True
    assert data["can_event_edit"] is True


def test_update_current_user(client, admin_auth_headers):
    response = client.put(
        "/api/accounts/ourself",
        headers=admin_auth_headers,
        json={"first_name": "Updated", "last_name": "Admin"},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["user"]["first_name"] == "Updated"
    assert data["user"]["last_name"] == "Admin"


def test_list_accounts_requires_can_users(client, user_auth_headers):
    response = client.get("/api/accounts/", headers=user_auth_headers)
    assert response.status_code == 403


def test_list_accounts_success(client, admin_auth_headers, admin_user, plain_user):
    response = client.get("/api/accounts/", headers=admin_auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data["total"] >= 2
    emails = {item["email"] for item in data["items"]}
    assert admin_user.email in emails
    assert plain_user.email in emails


def test_update_account_and_cannot_deactivate_self(client, admin_auth_headers, admin_user):
    response = client.put(
        f"/api/accounts/{admin_user.uuid}",
        headers=admin_auth_headers,
        json={"is_active": False},
    )
    assert response.status_code == 409
    assert "cannot deactivate your own account" in response.get_json()["message"].lower()


def test_delete_account_success(client, admin_auth_headers, permissions):
    target = create_user(
        email="delete.me@example.com",
        first_name="Delete",
        last_name="Me",
        password=VALID_PASSWORD,
    )
    response = client.delete(
        f"/api/accounts/{target.uuid}",
        headers=admin_auth_headers,
    )
    assert response.status_code == 200
    assert "deleted" in response.get_json()["message"].lower()


def test_delete_own_account_forbidden(client, admin_auth_headers, admin_user):
    response = client.delete(
        f"/api/accounts/{admin_user.uuid}",
        headers=admin_auth_headers,
    )
    assert response.status_code == 409


def test_grant_and_revoke_permission(client, admin_auth_headers, plain_user, permissions):
    catalog = client.get("/api/permissions/", headers=admin_auth_headers)
    assert catalog.status_code == 200
    codes = {item["code"] for item in catalog.get_json()["items"]}
    assert "can_recips" in codes

    grant = client.post(
        f"/api/accounts/{plain_user.uuid}/permissions",
        headers=admin_auth_headers,
        json={"permission_codes": ["can_recips"]},
    )
    assert grant.status_code == 200
    data = grant.get_json()
    assert "can_recips" in data["granted"]
    assert any(item["code"] == "can_recips" for item in data["permissions"])

    listed = client.get(
        f"/api/accounts/{plain_user.uuid}/permissions",
        headers=admin_auth_headers,
    )
    assert listed.status_code == 200
    assert any(item["code"] == "can_recips" for item in listed.get_json()["items"])

    detail = client.get(f"/api/accounts/{plain_user.uuid}", headers=admin_auth_headers)
    assert detail.status_code == 200
    assert "can_recips" in detail.get_json().get("permissions", [])

    revoke = client.delete(
        f"/api/accounts/{plain_user.uuid}/permissions/can_recips",
        headers=admin_auth_headers,
    )
    assert revoke.status_code == 200
    assert "can_recips" in revoke.get_json()["revoked"]

    after = client.get(
        f"/api/accounts/{plain_user.uuid}/permissions",
        headers=admin_auth_headers,
    )
    assert not any(item["code"] == "can_recips" for item in after.get_json()["items"])


def test_cannot_revoke_own_can_users(client, admin_auth_headers, admin_user):
    response = client.delete(
        f"/api/accounts/{admin_user.uuid}/permissions/can_users",
        headers=admin_auth_headers,
    )
    assert response.status_code == 409


def test_grant_permission_forbidden_without_can_permissions(client, user_auth_headers, plain_user):
    response = client.post(
        f"/api/accounts/{plain_user.uuid}/permissions",
        headers=user_auth_headers,
        json={"permission_codes": ["can_recips"]},
    )
    assert response.status_code == 403


def test_grant_permission_forbidden_with_only_can_users(client, plain_user, permissions):
    from tests.helpers import VALID_PASSWORD, auth_headers, create_user, login

    create_user(
        email="users.only.grant@example.com",
        first_name="Users",
        last_name="Only",
        password=VALID_PASSWORD,
        permission_codes=["can_users"],
    )
    login_response = login(client, "users.only.grant@example.com", VALID_PASSWORD)
    assert login_response.status_code == 200
    headers = auth_headers(login_response.get_json()["access_token"])

    response = client.post(
        f"/api/accounts/{plain_user.uuid}/permissions",
        headers=headers,
        json={"permission_codes": ["can_recips"]},
    )
    assert response.status_code == 403
