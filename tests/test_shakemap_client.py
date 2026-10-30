from datetime import datetime
from unittest.mock import MagicMock, patch

from app.utils.shakemap_client import ShakeMapError, delete_event, find_remote_event_id, sync_event


class _MagnitudeType:
    def __init__(self, code):
        self.code = code


class _EventMagnitude:
    def __init__(self, code, value):
        self.magnitude = _MagnitudeType(code)
        self.value = value


class _Event:
    def __init__(self, **overrides):
        self.id = 12
        self.is_automatic = True
        self.seiscomp_oid = "ies2026nrtc"
        self.origin_time = datetime(2026, 8, 5, 12, 30, 0)
        self.latitude = 41.7151
        self.longitude = 44.8271
        self.depth = 10.5
        self.location_ge = "თბილისის მახლობლად"
        self.location_en = None
        self.area = "local"
        self.iesdata_id = None
        self.event_magnitudes = [_EventMagnitude("ML", 3.4)]
        for key, value in overrides.items():
            setattr(self, key, value)


class _Response:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self.content = b"{}"
        self._payload = payload

    def json(self):
        return self._payload


def _enable(app):
    app.config["SHAKEMAP_API_URL"] = "https://shakemap.test"
    app.config["SHAKEMAP_API_KEY"] = "secret"
    app.config["SHAKEMAP_SSL_VERIFY"] = True


def test_sync_posts_event_then_starts_calculation(app):
    _enable(app)
    with patch("app.utils.shakemap_client.requests.post") as post:
        post.side_effect = [
            _Response(201, {"id": 9}),
            _Response(202, {"state": "queued"}),
        ]
        with app.app_context():
            result = sync_event(_Event(iesdata_id=539870))

    assert result["event_status"] == 201
    assert result["shakemap_status"] == 202
    event_call, shakemap_call = post.call_args_list
    assert event_call.args[0] == "https://shakemap.test/api/events"
    assert event_call.kwargs["json"] == {
        "seiscomp_oid": "ies2026nrtc",
        "origin_time": "2026-08-05T12:30:00",
        "latitude": 41.7151,
        "longitude": 44.8271,
        "depth": 10.5,
        "ml": 3.4,
        "event_id": 539870,
        "location_ge": "თბილისის მახლობლად",
        "area": "local",
    }
    assert event_call.kwargs["headers"]["X-API-Key"] == "secret"
    assert event_call.kwargs["verify"] is True
    assert event_call.kwargs["timeout"] == 20
    assert shakemap_call.args[0] == "https://shakemap.test/api/shakemap"
    assert shakemap_call.kwargs["json"] == {"seiscomp_oid": "ies2026nrtc"}


def test_sync_accepts_existing_shakemap_calculation(app):
    _enable(app)
    with patch("app.utils.shakemap_client.requests.post") as post:
        post.side_effect = [_Response(200, {}), _Response(409, {"detail": "running"})]
        with app.app_context():
            result = sync_event(_Event())
    assert result["shakemap_status"] == 409


def test_sync_sends_a_hand_added_event(app):
    _enable(app)
    with patch("app.utils.shakemap_client.requests.post") as post:
        post.side_effect = [_Response(201, {"id": 9}), _Response(202, {})]
        with app.app_context():
            result = sync_event(_Event(is_automatic=False))
    assert result["event_status"] == 201
    assert post.call_args_list[0].kwargs["json"]["ml"] == 3.4
    assert post.call_args_list[1].kwargs["json"] == {"seiscomp_oid": "ies2026nrtc"}


def test_sync_skips_events_without_oid_depth_or_ml(app):
    _enable(app)
    with patch("app.utils.shakemap_client.requests.post") as post:
        with app.app_context():
            assert sync_event(_Event(seiscomp_oid=None)) is None
            assert sync_event(_Event(event_magnitudes=[])) is None
            assert sync_event(_Event(event_magnitudes=[_EventMagnitude("MW", 3.2)])) is None
            assert sync_event(_Event(depth=None)) is None
    post.assert_not_called()


def test_sync_skips_when_shakemap_is_not_configured(app):
    app.config["SHAKEMAP_API_URL"] = ""
    app.config["SHAKEMAP_API_KEY"] = ""
    with patch("app.utils.shakemap_client.requests.post") as post:
        with app.app_context():
            assert sync_event(_Event()) is None
    post.assert_not_called()


def test_event_rejection_does_not_start_calculation(app):
    _enable(app)
    with patch("app.utils.shakemap_client.requests.post") as post:
        post.return_value = _Response(400, {"message": "bad origin"})
        with app.app_context():
            try:
                sync_event(_Event())
            except ShakeMapError as exc:
                assert exc.status == 400
                assert "/api/events failed" in str(exc)
            else:
                raise AssertionError("expected ShakeMapError")
    assert post.call_count == 1


def test_calculation_rejection_raises(app):
    _enable(app)
    with patch("app.utils.shakemap_client.requests.post") as post:
        post.side_effect = [_Response(201, {}), _Response(500, {"message": "down"})]
        with app.app_context():
            try:
                sync_event(_Event())
            except ShakeMapError as exc:
                assert exc.status == 500
            else:
                raise AssertionError("expected ShakeMapError")


def test_hand_added_magnitude_is_forwarded_and_a_shakemap_error_keeps_the_event(
    client, admin_auth_headers, app
):
    from app.models import Magnitude

    with app.app_context():
        if Magnitude.query.filter_by(code="ML").first() is None:
            Magnitude(code="ML", description="Local Magnitude").create()

    created = client.post(
        "/api/seismic_events/",
        headers=admin_auth_headers,
        json={
            "origin_time": "2026-08-05T12:30:00",
            "latitude": 41.7151,
            "longitude": 44.8271,
            "depth": 10.5,
            "seiscomp_oid": "ies2026nrtc",
        },
    )
    assert created.status_code == 201
    event = created.get_json()["event"]
    event_id = event["id"]
    assert event["is_automatic"] is False

    with patch("app.api.seismic_events.sync_event", side_effect=ShakeMapError("down")) as sync:
        added = client.post(
            f"/api/seismic_events/{event_id}/magnitudes",
            headers=admin_auth_headers,
            json={"magnitude_code": "ML", "value": 3.4},
        )

    assert added.status_code == 201
    sent = sync.call_args.args[0]
    assert sent.id == event_id
    assert sent.seiscomp_oid == "ies2026nrtc"
    assert sent.is_automatic is False

    detail = client.get(
        f"/api/seismic_events/event_id={event_id}",
        headers=admin_auth_headers,
    )
    assert detail.status_code == 200
    body = detail.get_json()
    assert body["magnitudes"][0]["value"] == 3.4
    assert body["seiscomp_oid"] == "ies2026nrtc"


def _product_response(status_code, content, content_type):
    response = MagicMock()
    response.status_code = status_code
    response.content = content
    response.headers = {"Content-Type": content_type}
    return response


def test_shakemap_product_is_proxied(client, admin_auth_headers, app):
    app.config["SHAKEMAP_API_URL"] = "https://shakemap.test"
    app.config["SHAKEMAP_API_KEY"] = "secret"
    app.config["SHAKEMAP_SSL_VERIFY"] = True
    payload = b'{"type":"FeatureCollection"}'

    with patch(
        "app.utils.shakemap_client.requests.get",
        return_value=_product_response(200, payload, "application/json"),
    ) as get:
        response = client.get(
            "/api/shakemap/product/cont_mi.json",
            query_string={"seiscomp_oid": "Origin/ies2026"},
            headers=admin_auth_headers,
        )

    assert response.status_code == 200
    assert response.data == payload
    assert response.mimetype == "application/json"
    assert get.call_args.args[0] == (
        "https://shakemap.test/api/shakemap/Origin%2Fies2026/product/cont_mi.json"
    )
    assert "X-API-Key" not in get.call_args.kwargs["headers"]


def test_unknown_shakemap_product_is_rejected(client, admin_auth_headers):
    response = client.get(
        "/api/shakemap/product/secret.txt",
        query_string={"seiscomp_oid": "ies2026nrtc"},
        headers=admin_auth_headers,
    )
    assert response.status_code == 400


def test_missing_shakemap_product_is_not_found(client, admin_auth_headers, app):
    app.config["SHAKEMAP_API_URL"] = "https://shakemap.test"
    app.config["SHAKEMAP_API_KEY"] = "secret"
    with patch(
        "app.utils.shakemap_client.requests.get",
        return_value=_product_response(404, b"", "application/json"),
    ):
        response = client.get(
            "/api/shakemap/product/cont_mi.json",
            query_string={"seiscomp_oid": "ies2026nrtc"},
            headers=admin_auth_headers,
        )
    assert response.status_code == 404


def test_shakemap_view_omits_missing_files(client, admin_auth_headers, app):
    app.config["SHAKEMAP_API_URL"] = "https://shakemap.test"
    app.config["SHAKEMAP_SSL_VERIFY"] = True

    def download(_base_url, _verify, _oid, filename, timeout=20):
        if filename == "cont_mi.json":
            return b'{"type":"FeatureCollection","features":[]}', "application/json"
        if filename == "mmi_legend.png":
            return b"png", "image/png"
        raise ShakeMapError("ShakeMap product not found.", 404)

    with patch("app.utils.shakemap_client._download_product", side_effect=download):
        response = client.get(
            "/api/shakemap/view",
            query_string={"seiscomp_oid": "ies2026rudf"},
            headers=admin_auth_headers,
        )

    assert response.status_code == 200
    body = response.get_json()
    assert body["layers"]["Intensity"]["type"] == "FeatureCollection"
    assert "PGA" not in body["layers"]
    assert body["info"] is None
    assert body["stations"] is None
    assert body["rupture"] is None
    assert body["has_legend"] is True


def test_shakemap_product_requires_login(client):
    response = client.get(
        "/api/shakemap/product/info.json",
        query_string={"seiscomp_oid": "ies2026nrtc"},
    )
    assert response.status_code == 401


def test_find_remote_event_id_matches_exact_oid(app):
    _enable(app)
    with patch("app.utils.shakemap_client.requests.request") as request:
        request.return_value = _Response(
            200,
            [
                {"id": 10, "seiscomp_oid": "ies2026rudu", "event_id": 1},
                {"id": 47, "seiscomp_oid": "ies2026rudf", "event_id": 588683},
            ],
        )
        with app.app_context():
            assert find_remote_event_id("ies2026rudf") == 47
            assert find_remote_event_id("ies2026ru") is None


def test_delete_event_uses_api_key_and_primary_key(app):
    _enable(app)

    def request(method, url, **kwargs):
        if method == "GET":
            return _Response(200, [{"id": 47, "seiscomp_oid": "ies2026rudf"}])
        if method == "DELETE":
            assert url == "https://shakemap.test/api/events/47"
            assert kwargs["headers"]["X-API-Key"] == "secret"
            return _Response(200, {"message": "deleted"})
        raise AssertionError(f"unexpected {method} {url}")

    with patch("app.utils.shakemap_client.requests.request", side_effect=request):
        with app.app_context():
            result = delete_event("ies2026rudf")
    assert result == {"id": 47, "deleted": True}


def test_delete_event_skips_when_remote_event_is_missing(app):
    _enable(app)
    with patch("app.utils.shakemap_client.requests.request") as request:
        request.return_value = _Response(200, [])
        with app.app_context():
            assert delete_event("ies2026missing") is None
    assert request.call_count == 1


def test_local_delete_also_deletes_on_shakemap(client, admin_auth_headers, app):
    created = client.post(
        "/api/seismic_events/",
        headers=admin_auth_headers,
        json={
            "origin_time": "2026-08-05T12:30:00",
            "latitude": 41.7151,
            "longitude": 44.8271,
            "depth": 10.5,
            "seiscomp_oid": "ies2026rudf",
        },
    )
    assert created.status_code == 201
    event_id = created.get_json()["event"]["id"]

    with patch(
        "app.api.seismic_events.delete_shakemap_event",
        return_value={"id": 47, "deleted": True},
    ) as remote_delete:
        deleted = client.delete(
            f"/api/seismic_events/event_id={event_id}",
            headers=admin_auth_headers,
        )

    assert deleted.status_code == 200
    remote_delete.assert_called_once_with("ies2026rudf")
    missing = client.get(
        f"/api/seismic_events/event_id={event_id}",
        headers=admin_auth_headers,
    )
    assert missing.status_code == 404
