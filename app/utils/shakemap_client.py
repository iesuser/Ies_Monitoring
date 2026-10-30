import json
import logging
import warnings
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote

import requests
from flask import current_app
from urllib3.exceptions import InsecureRequestWarning

logger = logging.getLogger("app.shakemap")

# Same statuses the SeisComp script accepted.
_EVENT_OK = (200, 201)
_SHAKEMAP_OK = (200, 201, 202, 409)


# Files the ShakeMap detail map loads from current/products.
PRODUCT_FILES = frozenset(
    {
        "info.json",
        "cont_mi.json",
        "cont_pga.json",
        "cont_pgv.json",
        "cont_psa0p3.json",
        "cont_psa1p0.json",
        "cont_psa3p0.json",
        "stationlist.json",
        "rupture.json",
        "mmi_legend.png",
    }
)

# Contour files drawn on the details map. Missing files are left out.
CONTOUR_FILES = (
    ("Intensity", "cont_mi.json"),
    ("PGA", "cont_pga.json"),
    ("PGV", "cont_pgv.json"),
    ("PSA 0.3s", "cont_psa0p3.json"),
    ("PSA 1.0s", "cont_psa1p0.json"),
    ("PSA 3.0s", "cont_psa3p0.json"),
)


class ShakeMapError(RuntimeError):
    """ShakeMap rejected the event or could not be reached."""

    def __init__(self, message, status=None):
        super().__init__(message)
        self.status = status


def _settings():
    url = (current_app.config.get("SHAKEMAP_API_URL") or "").strip().rstrip("/")
    api_key = (current_app.config.get("SHAKEMAP_API_KEY") or "").strip()
    verify = bool(current_app.config.get("SHAKEMAP_SSL_VERIFY", False))
    return url, api_key, verify


def _local_magnitude(event):
    """ShakeMap POST /api/events requires a single ml value."""
    for item in event.event_magnitudes:
        code = item.magnitude.code if item.magnitude else None
        if code and code.upper() == "ML":
            return item.value
    return None


def _payload(event):
    """Body for ShakeMap POST /api/events.

    Required there: seiscomp_oid, origin_time, latitude, longitude, depth, ml.
    """
    ml = _local_magnitude(event)
    if ml is None or event.depth is None or event.origin_time is None:
        return None

    payload = {
        "seiscomp_oid": event.seiscomp_oid,
        "origin_time": event.origin_time.isoformat(),
        "latitude": event.latitude,
        "longitude": event.longitude,
        "depth": event.depth,
        "ml": ml,
    }
    # ShakeMap's event_id is their manual id; we store that as iesdata_id.
    if event.iesdata_id is not None:
        payload["event_id"] = event.iesdata_id
    for field in ("location_ge", "location_en", "area"):
        value = getattr(event, field, None)
        if value:
            payload[field] = value
    return payload


def _request(method, url, *, headers, timeout, verify, payload=None, params=None):
    try:
        response = requests.request(
            method,
            url,
            json=payload,
            params=params,
            headers=headers,
            timeout=timeout,
            verify=verify,
        )
    except requests.RequestException as exc:
        raise ShakeMapError(f"Could not reach ShakeMap: {exc}") from exc

    try:
        data = response.json() if response.content else {}
    except ValueError:
        data = {}
    return response.status_code, data


def _post(url, payload, headers, timeout, verify):
    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=timeout,
            verify=verify,
        )
    except requests.RequestException as exc:
        raise ShakeMapError(f"Could not reach ShakeMap: {exc}") from exc

    try:
        data = response.json() if response.content else {}
    except ValueError:
        data = {}
    return response.status_code, data


def find_remote_event_id(seiscomp_oid, timeout=20):
    """Return ShakeMap's primary key id for an exact seiscomp_oid, or None.

    Filter results only expose their manual event_id, so we use GET /api/events
    and match seiscomp_oid exactly. Substring matches are ignored.
    """
    oid = (seiscomp_oid or "").strip()
    if not oid:
        return None

    base_url, _api_key, verify = _settings()
    if not base_url:
        raise ShakeMapError("SHAKEMAP_API_URL is not configured.", 503)

    if not verify:
        warnings.simplefilter("ignore", InsecureRequestWarning)

    status, data = _request(
        "GET",
        f"{base_url}/api/events",
        headers={"Accept": "application/json"},
        timeout=timeout,
        verify=verify,
    )
    if status != 200:
        raise ShakeMapError(f"/api/events failed ({status}): {data}", status)
    if not isinstance(data, list):
        raise ShakeMapError(f"/api/events returned an unexpected body: {data}", 502)

    matches = [item for item in data if isinstance(item, dict) and item.get("seiscomp_oid") == oid]
    if not matches:
        return None
    remote_id = matches[0].get("id")
    if remote_id is None:
        raise ShakeMapError(
            f"ShakeMap event for {oid} has no primary key id: {matches[0]}",
            502,
        )
    return remote_id


def delete_event(seiscomp_oid, timeout=20):
    """Find the ShakeMap event by seiscomp_oid and DELETE /api/events/{id}.

    Uses the same X-API-Key as create. Returns {"id": remote_id, "deleted": True}
    when removed, None when there is no SeisComP id, ShakeMap is not configured,
    or the event is already gone.
    """
    oid = (seiscomp_oid or "").strip()
    if not oid:
        return None

    base_url, api_key, verify = _settings()
    if not base_url or not api_key:
        logger.warning(
            "ShakeMap delete skipped: set SHAKEMAP_API_URL and SHAKEMAP_API_KEY. seiscomp_oid=%s",
            oid,
        )
        return None

    remote_id = find_remote_event_id(oid, timeout=timeout)
    if remote_id is None:
        logger.info("ShakeMap delete skipped: no remote event for seiscomp_oid=%s", oid)
        return None

    if not verify:
        warnings.simplefilter("ignore", InsecureRequestWarning)

    status, data = _request(
        "DELETE",
        f"{base_url}/api/events/{remote_id}",
        headers={
            "X-API-Key": api_key,
            "Accept": "application/json",
        },
        timeout=timeout,
        verify=verify,
    )
    if status == 404:
        logger.info(
            "ShakeMap event already gone: remote_id=%s seiscomp_oid=%s",
            remote_id,
            oid,
        )
        return {"id": remote_id, "deleted": False}
    if status not in (200, 204):
        raise ShakeMapError(
            f"/api/events/{remote_id} delete failed ({status}): {data}",
            status,
        )

    logger.info(
        "ShakeMap delete success: remote_id=%s seiscomp_oid=%s",
        remote_id,
        oid,
    )
    return {"id": remote_id, "deleted": True}


def _download_product(base_url, verify, seiscomp_oid, filename, timeout=20):
    """Download one public ShakeMap product. Returns (bytes, content_type)."""
    if filename not in PRODUCT_FILES:
        raise ShakeMapError("Unknown ShakeMap product.", 400)
    oid = (seiscomp_oid or "").strip()
    if not oid:
        raise ShakeMapError("seiscomp_oid is required.", 400)
    if not base_url:
        raise ShakeMapError("SHAKEMAP_API_URL is not configured.", 503)

    if not verify:
        warnings.simplefilter("ignore", InsecureRequestWarning)

    url = f"{base_url}/api/shakemap/{quote(oid, safe='')}/product/{quote(filename, safe='')}"
    try:
        response = requests.get(
            url,
            headers={"Accept": "*/*"},
            timeout=timeout,
            verify=verify,
        )
    except requests.RequestException as exc:
        raise ShakeMapError(f"Could not reach ShakeMap: {exc}") from exc

    if response.status_code == 404:
        raise ShakeMapError("ShakeMap product not found.", 404)
    if response.status_code != 200:
        raise ShakeMapError(
            f"ShakeMap product failed ({response.status_code}).",
            response.status_code,
        )

    content_type = (response.headers.get("Content-Type") or "application/octet-stream").split(";")[0].strip()
    return response.content, content_type or "application/octet-stream"


def fetch_product(seiscomp_oid, filename, timeout=20):
    """Download one calculated ShakeMap product. Returns (bytes, content_type)."""
    base_url, _api_key, verify = _settings()
    return _download_product(base_url, verify, seiscomp_oid, filename, timeout)


def _read_json_product(downloaded):
    if downloaded is None:
        return None
    content, _content_type = downloaded
    try:
        return json.loads(content)
    except ValueError:
        return None


def load_view(seiscomp_oid, timeout=20):
    """Collect the products the details map can draw.

    Files ShakeMap does not have for this event are omitted. Product reads are
    public on ShakeMap, so no API key is sent.
    """
    base_url, _api_key, verify = _settings()
    oid = (seiscomp_oid or "").strip()
    if not oid:
        raise ShakeMapError("seiscomp_oid is required.", 400)
    if not base_url:
        raise ShakeMapError("SHAKEMAP_API_URL is not configured.", 503)

    filenames = [
        "info.json",
        *[filename for _name, filename in CONTOUR_FILES],
        "stationlist.json",
        "rupture.json",
        "mmi_legend.png",
    ]

    def _one(filename):
        try:
            return filename, _download_product(base_url, verify, oid, filename, timeout)
        except ShakeMapError as exc:
            if exc.status == 404:
                return filename, None
            raise

    with ThreadPoolExecutor(max_workers=6) as pool:
        downloaded = dict(pool.map(_one, filenames))

    layers = {}
    for name, filename in CONTOUR_FILES:
        parsed = _read_json_product(downloaded.get(filename))
        if parsed is not None:
            layers[name] = parsed

    return {
        "info": _read_json_product(downloaded.get("info.json")),
        "layers": layers,
        "stations": _read_json_product(downloaded.get("stationlist.json")),
        "rupture": _read_json_product(downloaded.get("rupture.json")),
        "has_legend": downloaded.get("mmi_legend.png") is not None,
    }


def sync_event(event, timeout=20):
    """Create the event on ShakeMap, then start calculation for its SeisComP id.

    POST /api/events, then POST /api/shakemap with {"seiscomp_oid": ...}.
    Runs for any saved event that has a SeisComP id, depth, and ML, including
    one added by hand. Returns None when there is nothing to send (including
    when ShakeMap is not configured). Raises ShakeMapError when a call fails.
    """
    if not (event.seiscomp_oid or "").strip():
        return None
    if not event.event_magnitudes:
        return None

    payload = _payload(event)
    if payload is None:
        logger.warning(
            "ShakeMap sync skipped: ML and depth are required. event_id=%s seiscomp_oid=%s",
            event.id,
            event.seiscomp_oid,
        )
        return None

    base_url, api_key, verify = _settings()
    if not base_url or not api_key:
        logger.warning(
            "ShakeMap sync skipped: set SHAKEMAP_API_URL and SHAKEMAP_API_KEY. event_id=%s",
            event.id,
        )
        return None

    if not verify:
        logger.warning("ShakeMap SSL verification disabled (SHAKEMAP_SSL_VERIFY=false)")
        warnings.simplefilter("ignore", InsecureRequestWarning)

    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    event_status, event_data = _post(
        f"{base_url}/api/events",
        payload,
        headers,
        timeout,
        verify,
    )
    if event_status not in _EVENT_OK:
        raise ShakeMapError(
            f"/api/events failed ({event_status}): {event_data}",
            event_status,
        )

    shakemap_status, shakemap_data = _post(
        f"{base_url}/api/shakemap",
        {"seiscomp_oid": event.seiscomp_oid},
        headers,
        timeout,
        verify,
    )
    if shakemap_status not in _SHAKEMAP_OK:
        raise ShakeMapError(
            f"/api/shakemap failed ({shakemap_status}): {shakemap_data}",
            shakemap_status,
        )

    result = {
        "event_status": event_status,
        "event_data": event_data,
        "shakemap_status": shakemap_status,
        "shakemap_data": shakemap_data,
    }
    logger.info(
        "ShakeMap sync success: event_id=%s seiscomp_oid=%s event_status=%s shakemap_status=%s",
        event.id,
        event.seiscomp_oid,
        event_status,
        shakemap_status,
    )
    return result
