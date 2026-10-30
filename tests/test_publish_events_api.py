from unittest.mock import patch

from app.models import Magnitude, PublishedEvent
from tests.helpers import VALID_PASSWORD, auth_headers, create_user, login


def _seed_magnitude(code="ML", description="Local Magnitude"):
    existing = Magnitude.query.filter_by(code=code).first()
    if existing:
        return existing
    magnitude = Magnitude(code=code, description=description)
    magnitude.create()
    return magnitude


def _create_event_with_ml(client, headers, *, is_automatic=False, origin_time="2026-08-05T12:30:00"):
    create_response = client.post(
        "/api/seismic_events/",
        headers=headers,
        json={
            "origin_time": origin_time,
            "latitude": 41.7151,
            "longitude": 44.8271,
            "depth": 10.5,
            "location_ge": "თბილისის მახლობლად",
            "location_en": "Near Tbilisi",
            "is_automatic": is_automatic,
        },
    )
    assert create_response.status_code == 201
    event = create_response.get_json()["event"]
    event_id = event["id"]
    assert event["is_published"] is False

    mag_response = client.post(
        f"/api/seismic_events/{event_id}/magnitudes",
        headers=headers,
        json={"magnitude_code": "ML", "value": 3.4},
    )
    assert mag_response.status_code == 201
    return event_id


def test_list_published_events_is_public(client, admin_auth_headers, app):
    with app.app_context():
        _seed_magnitude("ML")
        assert client.get("/api/publish_events/").status_code == 200
        assert client.get("/api/publish_events/").get_json() == {
            "items": [],
            "total": 0,
            "limit": 100,
        }

    event_id = _create_event_with_ml(client, admin_auth_headers, is_automatic=True)
    with patch("app.api.publish_events.publish_eq", return_value="ok-publish"):
        publish_response = client.post(
            f"/api/publish_events/publish/{event_id}",
            headers=admin_auth_headers,
        )
    assert publish_response.status_code == 200

    # No Authorization header — public endpoint.
    listed = client.get("/api/publish_events/")
    assert listed.status_code == 200
    data = listed.get_json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["event_id"] == event_id
    assert data["items"][0]["event"]["id"] == event_id
    assert data["items"][0]["event"]["is_published"] is True
    assert data["items"][0]["published_at"] is not None
    assert "wp_response" not in data["items"][0]

    assert client.get("/api/publish_events/", query_string={"limit": 201}).status_code == 400


def test_published_events_page_is_public(client):
    redirect = client.get("/published_events")
    assert redirect.status_code == 302
    assert redirect.headers["Location"].endswith("/en/published_events")

    page = client.get("/ka/published_events")
    assert page.status_code == 200
    assert b"publishedTableBody" in page.data
    assert b"publishedEvents.js" in page.data


def test_index_view_events_links_to_published_page(client):
    page = client.get("/en/")
    assert page.status_code == 200
    assert b'href="/en/published_events"' in page.data


def test_publish_requires_permission(client, user_auth_headers, admin_auth_headers, app):
    with app.app_context():
        _seed_magnitude("ML")
    event_id = _create_event_with_ml(client, admin_auth_headers)

    response = client.post(
        f"/api/publish_events/publish/{event_id}",
        headers=user_auth_headers,
    )
    assert response.status_code == 403


def test_publish_and_unpublish_with_jwt(client, admin_auth_headers, app):
    with app.app_context():
        _seed_magnitude("ML")
    event_id = _create_event_with_ml(client, admin_auth_headers, is_automatic=True)

    with patch("app.api.publish_events.publish_eq", return_value="ok-publish") as mock_publish:
        response = client.post(
            f"/api/publish_events/publish/{event_id}",
            headers=admin_auth_headers,
        )

    assert response.status_code == 200
    data = response.get_json()
    assert data["published"] is True
    assert data["wp_response"] == "ok-publish"
    assert data["event"]["is_published"] is True
    assert data["event"]["published_at"] is not None

    mock_publish.assert_called_once()
    kwargs = mock_publish.call_args.kwargs
    assert kwargs["eq_id"] == event_id
    assert kwargs["eq_type"] == "A"
    assert kwargs["important"] == 0
    assert kwargs["description_ge"] == "თბილისის მახლობლად"
    assert kwargs["description_en"] == "Near Tbilisi"
    assert kwargs["region_ge"] == "თბილისის მახლობლად"
    assert kwargs["region_en"] == "Near Tbilisi"
    assert kwargs["mag"] == 3.4
    assert kwargs["mag_type"] == "ML"

    with app.app_context():
        assert PublishedEvent.query.filter_by(event_id=event_id).count() == 1

    blocked = client.delete(
        f"/api/seismic_events/event_id={event_id}",
        headers=admin_auth_headers,
    )
    assert blocked.status_code == 409
    assert "Unpublish" in blocked.get_json()["message"]
    with app.app_context():
        assert PublishedEvent.query.filter_by(event_id=event_id).count() == 1

    with patch("app.api.publish_events.unpublish_eq", return_value="ok-unpublish") as mock_unpublish:
        unpublish_response = client.post(
            f"/api/publish_events/unpublish/{event_id}",
            headers=admin_auth_headers,
        )

    assert unpublish_response.status_code == 200
    unpublish_data = unpublish_response.get_json()
    assert unpublish_data["published"] is False
    assert unpublish_data["event"]["is_published"] is False
    mock_unpublish.assert_called_once_with(eq_id=event_id, code="test-wp-publish-code")

    with app.app_context():
        assert PublishedEvent.query.filter_by(event_id=event_id).count() == 0

    deleted = client.delete(
        f"/api/seismic_events/event_id={event_id}",
        headers=admin_auth_headers,
    )
    assert deleted.status_code == 200


def test_publish_manual_type_and_service_api_key(client, admin_auth_headers, app):
    with app.app_context():
        _seed_magnitude("ML")
    event_id = _create_event_with_ml(client, admin_auth_headers, is_automatic=False)

    service_response = client.post(
        "/api/services/",
        headers=admin_auth_headers,
        json={
            "name": "eq-publisher",
            "description": "Publishes earthquakes",
            "permissions": ["can_event_publish"],
        },
    )
    assert service_response.status_code == 201
    api_key = service_response.get_json()["api_key"]
    service_headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    with patch("app.api.publish_events.publish_eq", return_value="service-ok") as mock_publish:
        response = client.post(
            f"/api/publish_events/publish/{event_id}",
            headers=service_headers,
        )

    assert response.status_code == 200
    assert mock_publish.call_args.kwargs["eq_type"] == "M"
    assert mock_publish.call_args.kwargs["important"] == 0


def test_publish_rejects_event_without_magnitude(client, admin_auth_headers, app):
    create_response = client.post(
        "/api/seismic_events/",
        headers=admin_auth_headers,
        json={
            "origin_time": "2026-08-05T12:30:00",
            "latitude": 41.7151,
            "longitude": 44.8271,
        },
    )
    assert create_response.status_code == 201
    event_id = create_response.get_json()["event"]["id"]

    with patch("app.api.publish_events.publish_eq") as mock_publish:
        response = client.post(
            f"/api/publish_events/publish/{event_id}",
            headers=admin_auth_headers,
        )

    assert response.status_code == 400
    mock_publish.assert_not_called()


def test_publish_permission_only_user_can_publish(client, permissions, admin_auth_headers, app):
    with app.app_context():
        _seed_magnitude("ML")

    create_user(
        email="publisher@example.com",
        first_name="Pub",
        last_name="Lisher",
        password=VALID_PASSWORD,
        permission_codes=["can_event_publish"],
    )
    # Publisher cannot create events; admin creates one for them.
    event_id = _create_event_with_ml(client, admin_auth_headers)

    login_response = login(client, "publisher@example.com", VALID_PASSWORD)
    assert login_response.status_code == 200
    headers = auth_headers(login_response.get_json()["access_token"])

    with patch("app.api.publish_events.publish_eq", return_value="pub-ok"):
        response = client.post(
            f"/api/publish_events/publish/{event_id}",
            headers=headers,
        )
    assert response.status_code == 200


def test_published_list_is_ordered_by_earthquake_time_and_hides_audit(client, admin_auth_headers, app):
    with app.app_context():
        _seed_magnitude("ML")
    newer = _create_event_with_ml(client, admin_auth_headers, origin_time="2026-09-01T10:00:00")
    older = _create_event_with_ml(client, admin_auth_headers, origin_time="2026-07-01T10:00:00")

    # Publish the newer earthquake first, so publish order and earthquake order differ.
    with patch("app.api.publish_events.publish_eq", return_value="ok"):
        for event_id in (newer, older):
            response = client.post(
                f"/api/publish_events/publish/{event_id}", headers=admin_auth_headers
            )
            assert response.status_code == 200

    items = client.get("/api/publish_events/").get_json()["items"]
    assert [item["event_id"] for item in items] == [newer, older]
    for field in ("created_by", "updated_by", "updated_at"):
        assert field not in items[0]["event"]
