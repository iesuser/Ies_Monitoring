from app.models import Magnitude


def _seed_magnitude(code="MW", description="Moment Magnitude"):
    existing = Magnitude.query.filter_by(code=code).first()
    if existing:
        return existing
    magnitude = Magnitude(code=code, description=description)
    magnitude.create()
    return magnitude


def test_list_seismic_events_requires_permission(client, user_auth_headers):
    response = client.get("/api/seismic_events/", headers=user_auth_headers)
    assert response.status_code == 403


def test_create_list_update_delete_seismic_event(client, admin_auth_headers, app):
    create_response = client.post(
        "/api/seismic_events/",
        headers=admin_auth_headers,
        json={
            "origin_time": "2026-08-05T12:30:00",
            "latitude": 41.7151,
            "longitude": 44.8271,
            "depth": 10.5,
            "location_en": "Near Tbilisi",
            "area": "Georgia",
        },
    )
    assert create_response.status_code == 201
    event = create_response.get_json()["event"]
    event_id = event["id"]
    assert event["latitude"] == 41.7151
    assert event["magnitudes"] == []
    assert event["beachball"] is None

    list_response = client.get("/api/seismic_events/", headers=admin_auth_headers)
    assert list_response.status_code == 200
    assert list_response.get_json()["total"] >= 1

    update_response = client.put(
        f"/api/seismic_events/{event_id}",
        headers=admin_auth_headers,
        json={"location_en": "Tbilisi region", "depth": 12.0},
    )
    assert update_response.status_code == 200
    updated = update_response.get_json()["event"]
    assert updated["location_en"] == "Tbilisi region"
    assert updated["depth"] == 12.0

    delete_response = client.delete(
        f"/api/seismic_events/{event_id}",
        headers=admin_auth_headers,
    )
    assert delete_response.status_code == 200


def test_event_magnitude_and_beachball_crud(client, admin_auth_headers, app):
    with app.app_context():
        magnitude = _seed_magnitude("MW")
        magnitude_id = magnitude.id

    create_response = client.post(
        "/api/seismic_events/",
        headers=admin_auth_headers,
        json={
            "origin_time": "2026-08-05T14:00:00",
            "latitude": 41.8,
            "longitude": 44.9,
            "depth": 8.0,
        },
    )
    assert create_response.status_code == 201
    event_id = create_response.get_json()["event"]["id"]

    mag_response = client.post(
        f"/api/seismic_events/{event_id}/magnitudes",
        headers=admin_auth_headers,
        json={"magnitude_code": "MW", "value": 4.2},
    )
    assert mag_response.status_code == 201
    event_magnitude = mag_response.get_json()["event_magnitude"]
    event_magnitude_id = event_magnitude["id"]
    assert event_magnitude["value"] == 4.2
    assert event_magnitude["magnitude"]["code"] == "MW"

    duplicate_mag = client.post(
        f"/api/seismic_events/{event_id}/magnitudes",
        headers=admin_auth_headers,
        json={"magnitude_id": magnitude_id, "value": 4.5},
    )
    assert duplicate_mag.status_code == 409

    update_mag = client.put(
        f"/api/seismic_events/magnitudes/{event_magnitude_id}",
        headers=admin_auth_headers,
        json={"value": 4.7},
    )
    assert update_mag.status_code == 200
    assert update_mag.get_json()["event_magnitude"]["value"] == 4.7

    beachball_create = client.post(
        f"/api/seismic_events/{event_id}/beachball",
        headers=admin_auth_headers,
        json={"rake": 90.0, "dip": 45.0, "strike": 180.0},
    )
    assert beachball_create.status_code == 201
    assert beachball_create.get_json()["beachball"]["strike"] == 180.0

    beachball_dup = client.post(
        f"/api/seismic_events/{event_id}/beachball",
        headers=admin_auth_headers,
        json={"rake": 10.0},
    )
    assert beachball_dup.status_code == 409

    beachball_update = client.put(
        f"/api/seismic_events/{event_id}/beachball",
        headers=admin_auth_headers,
        json={"strike": 200.0, "beachball_path": "/static/bb.png"},
    )
    assert beachball_update.status_code == 200
    beachball = beachball_update.get_json()["beachball"]
    assert beachball["strike"] == 200.0
    assert beachball["beachball_path"] == "/static/bb.png"

    get_event = client.get(f"/api/seismic_events/{event_id}", headers=admin_auth_headers)
    assert get_event.status_code == 200
    detail = get_event.get_json()
    assert len(detail["magnitudes"]) == 1
    assert detail["beachball"]["strike"] == 200.0

    delete_mag = client.delete(
        f"/api/seismic_events/magnitudes/{event_magnitude_id}",
        headers=admin_auth_headers,
    )
    assert delete_mag.status_code == 200

    delete_beachball = client.delete(
        f"/api/seismic_events/{event_id}/beachball",
        headers=admin_auth_headers,
    )
    assert delete_beachball.status_code == 200

    catalog = client.get("/api/seismic_events/magnitude_types", headers=admin_auth_headers)
    assert catalog.status_code == 200
    assert catalog.get_json()["total"] >= 1


def test_filter_seismic_events(client, admin_auth_headers, app):
    with app.app_context():
        _seed_magnitude("MW")
        _seed_magnitude("ML", "Local Magnitude")

    first = client.post(
        "/api/seismic_events/",
        headers=admin_auth_headers,
        json={
            "origin_time": "2026-08-01T10:00:00",
            "latitude": 41.7,
            "longitude": 44.8,
            "depth": 5.0,
            "seiscomp_oid": "Origin/filter-test-1",
            "iesdata_id": "IES-2026-0001",
            "location_en": "Near Tbilisi",
            "area": "Georgia",
        },
    )
    assert first.status_code == 201
    first_id = first.get_json()["event"]["id"]

    second = client.post(
        "/api/seismic_events/",
        headers=admin_auth_headers,
        json={
            "origin_time": "2026-08-10T18:00:00",
            "latitude": 42.1,
            "longitude": 43.2,
            "depth": 25.0,
            "seiscomp_oid": "Origin/filter-test-2",
            "iesdata_id": "IES-2026-0099",
            "location_en": "Near Kutaisi",
            "area": "Imereti",
        },
    )
    assert second.status_code == 201
    second_id = second.get_json()["event"]["id"]

    client.post(
        f"/api/seismic_events/{first_id}/magnitudes",
        headers=admin_auth_headers,
        json={"magnitude_code": "MW", "value": 3.1},
    )
    client.post(
        f"/api/seismic_events/{second_id}/magnitudes",
        headers=admin_auth_headers,
        json={"magnitude_code": "MW", "value": 5.4},
    )

    by_id = client.post(
        "/api/seismic_events/filter",
        headers=admin_auth_headers,
        json={"event_id": first_id},
    )
    assert by_id.status_code == 200
    assert by_id.get_json()["total"] == 1
    assert by_id.get_json()["items"][0]["id"] == first_id

    by_ies = client.post(
        "/api/seismic_events/filter",
        headers=admin_auth_headers,
        json={"iesdata_id": "2026-0001"},
    )
    assert by_ies.status_code == 200
    assert by_ies.get_json()["total"] == 1
    assert by_ies.get_json()["items"][0]["id"] == first_id

    by_oid = client.post(
        "/api/seismic_events/filter",
        headers=admin_auth_headers,
        json={"seiscomp_oid": "filter-test-2"},
    )
    assert by_oid.status_code == 200
    assert by_oid.get_json()["total"] == 1
    assert by_oid.get_json()["items"][0]["id"] == second_id

    by_location = client.post(
        "/api/seismic_events/filter",
        headers=admin_auth_headers,
        json={"location": "tbilisi"},
    )
    assert by_location.status_code == 200
    assert by_location.get_json()["total"] == 1
    assert by_location.get_json()["items"][0]["id"] == first_id

    by_area = client.post(
        "/api/seismic_events/filter",
        headers=admin_auth_headers,
        json={"area": "Imereti"},
    )
    assert by_area.status_code == 200
    assert by_area.get_json()["total"] == 1

    by_depth = client.post(
        "/api/seismic_events/filter",
        headers=admin_auth_headers,
        json={"depth_min": 20, "depth_max": 30},
    )
    assert by_depth.status_code == 200
    ids = {item["id"] for item in by_depth.get_json()["items"]}
    assert second_id in ids
    assert first_id not in ids

    by_date = client.post(
        "/api/seismic_events/filter",
        headers=admin_auth_headers,
        json={
            "date_from": "2026-08-05T00:00:00",
            "date_to": "2026-08-15T00:00:00",
        },
    )
    assert by_date.status_code == 200
    ids = {item["id"] for item in by_date.get_json()["items"]}
    assert second_id in ids
    assert first_id not in ids

    by_mag = client.post(
        "/api/seismic_events/filter",
        headers=admin_auth_headers,
        json={"magnitude": "MW", "magnitude_min": 5, "magnitude_max": 6},
    )
    assert by_mag.status_code == 200
    assert by_mag.get_json()["total"] == 1
    assert by_mag.get_json()["items"][0]["id"] == second_id

    invalid_range = client.post(
        "/api/seismic_events/filter",
        headers=admin_auth_headers,
        json={"magnitude_min": 6, "magnitude_max": 3},
    )
    assert invalid_range.status_code == 400
