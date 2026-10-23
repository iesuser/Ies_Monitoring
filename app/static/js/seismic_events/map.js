(function () {
    // Gori, so the initial view is centred on it rather than on Georgia's geometric centre.
    const GEORGIA_CENTER = { lat: 41.98, lng: 44.11 };
    // Georgia's width/height in degrees; the initial view is this span around GEORGIA_CENTER.
    const GEORGIA_SPAN = { lat: 2.54, lng: 6.7 };
    const DEFAULT_ZOOM = 7;
    // Zoom levels to step back from the tight Georgia fit, leaving some surroundings visible.
    const INITIAL_ZOOM_OUT = 0.5;
    const FOCUS_ZOOM = 10;
    const RECENT_DAYS = 60;
    const DAY_MS = 24 * 60 * 60 * 1000;
    const MARKER_ICONS = {
        latest: { url: "/static/images/earthquake_latest.gif", size: 34 },
        recent: { url: "/static/images/earthquake_red.svg", size: 16 },
        old: { url: "/static/images/earthquake_yellow.svg", size: 14 },
    };

    let map = null;
    let infoWindow = null;
    let markers = [];
    let pendingEvents = null;
    let authFailed = false;
    const markersById = new Map();

    function t(key, fallback) {
        return window.I18n ? window.I18n.t(key, fallback) : fallback;
    }

    function escapeHtml(value) {
        return String(value ?? "")
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#39;");
    }

    function isGoogleMapsReady() {
        return Boolean(window.google?.maps?.Map);
    }

    function ensureMap() {
        if (map || authFailed || !isGoogleMapsReady()) {
            return map;
        }

        const mapElement = document.getElementById("map");
        if (!mapElement) {
            return null;
        }

        map = new google.maps.Map(mapElement, {
            center: GEORGIA_CENTER,
            zoom: DEFAULT_ZOOM,
            mapTypeId: google.maps.MapTypeId.HYBRID,
            // Lets fitBounds use e.g. zoom 6.7 so Georgia fills the frame instead of rounding down to 6.
            isFractionalZoomEnabled: true,
            mapTypeControl: false,
            streetViewControl: false,
            fullscreenControl: true,
            gestureHandling: "cooperative",
        });
        infoWindow = new google.maps.InfoWindow();
        map.fitBounds(
            {
                south: GEORGIA_CENTER.lat - GEORGIA_SPAN.lat / 2,
                west: GEORGIA_CENTER.lng - GEORGIA_SPAN.lng / 2,
                north: GEORGIA_CENTER.lat + GEORGIA_SPAN.lat / 2,
                east: GEORGIA_CENTER.lng + GEORGIA_SPAN.lng / 2,
            },
            0,
        );
        google.maps.event.addListenerOnce(map, "idle", () => {
            map.setZoom(map.getZoom() - INITIAL_ZOOM_OUT);
        });
        return map;
    }

    function magnitudeLevel(value) {
        if (value >= 5) return "major";
        if (value >= 4) return "strong";
        if (value >= 3) return "moderate";
        return "minor";
    }

    function formatPopup(event, magnitude = window.getEventMagnitude?.(event)) {
        const lang = window.I18n?.getLanguage?.() || "en";
        const location =
            (lang === "ka" ? event.location_ge : event.location_en) ||
            event.location_en ||
            event.location_ge ||
            event.area ||
            "—";
        const magHtml = magnitude
            ? `<span class="published-mag published-mag-${magnitudeLevel(magnitude.value)}">
                    <span class="published-mag-value">${escapeHtml(magnitude.value.toFixed(1))}</span>
                    <span class="published-mag-code">${escapeHtml(magnitude.code || "")}</span>
               </span>`
            : `<span class="published-mag published-mag-minor"><span class="published-mag-value">—</span></span>`;

        const timeMatch = String(event.origin_time || "").match(
            /^(\d{4}-\d{2}-\d{2})[T\s](\d{2}:\d{2}:\d{2})/
        );
        const timeHtml = timeMatch
            ? `<div class="map-popup-date">${timeMatch[1]}</div>
               <div class="map-popup-time">${timeMatch[2]} <span>UTC</span></div>`
            : `<div class="map-popup-date">${escapeHtml(event.origin_time || "—")}</div>`;

        const depth = Number(event.depth);
        const hasDepth = event.depth !== null && event.depth !== undefined && Number.isFinite(depth);
        const depthHtml = hasDepth
            ? `<span><i class="fa-solid fa-arrow-down-long" aria-hidden="true"></i>
                    ${escapeHtml(t("events.table.depth_km", "Depth (km)"))}: <strong>${depth.toFixed(1)}</strong></span>`
            : "";

        return `
            <div class="map-popup">
                <div class="map-popup-head">
                    ${magHtml}
                    <div class="map-popup-when">${timeHtml}</div>
                </div>
                <div class="map-popup-location">
                    <i class="fa-solid fa-location-dot" aria-hidden="true"></i>
                    <span>${escapeHtml(location)}</span>
                </div>
                <div class="map-popup-meta">
                    ${depthHtml}
                    <span class="map-popup-id">#${escapeHtml(event.id)}</span>
                </div>
            </div>
        `;
    }

    function clearMarkers() {
        markers.forEach((marker) => marker.setMap(null));
        markers = [];
        markersById.clear();
        infoWindow?.close();
    }

    function openMarker(marker) {
        infoWindow.setContent(marker.popupHtml);
        infoWindow.open({ map, anchor: marker });
    }

    // The API sends origin_time as naive UTC, which Date.parse would read as local time.
    function originTimeMs(value) {
        const raw = String(value ?? "").trim();
        if (!raw) {
            return NaN;
        }
        const hasZone = /(?:Z|[+-]\d{2}:?\d{2})$/i.test(raw);
        return Date.parse(hasZone ? raw : `${raw.replace(" ", "T")}Z`);
    }

    function markerKind(timeMs, isLatest, nowMs) {
        if (isLatest) {
            return "latest";
        }
        if (!Number.isFinite(timeMs)) {
            return "old";
        }
        return nowMs - timeMs <= RECENT_DAYS * DAY_MS ? "recent" : "old";
    }

    function markerIcon(kind) {
        const { url, size } = MARKER_ICONS[kind];
        return {
            url,
            scaledSize: new google.maps.Size(size, size),
            anchor: new google.maps.Point(size / 2, size / 2),
        };
    }

    // `options.latestId` names the overall newest event; the given events may be just one page.
    // Without it, the newest of the given events is used.
    function updateMapMarkers(events, options = {}) {
        if (!ensureMap()) {
            // Google Maps loads asynchronously; render once it is ready.
            pendingEvents = { events: Array.isArray(events) ? events : [], options };
            return;
        }

        clearMarkers();

        const located = (Array.isArray(events) ? events : [])
            .map((event) => ({
                event,
                lat: Number(event.latitude),
                lng: Number(event.longitude),
                timeMs: originTimeMs(event.origin_time),
            }))
            .filter(({ lat, lng }) => Number.isFinite(lat) && Number.isFinite(lng));

        let latest = null;
        if ("latestId" in options) {
            const latestKey = options.latestId === null ? null : String(options.latestId);
            latest = located.find((item) => String(item.event.id) === latestKey) || null;
        } else {
            located.forEach((item) => {
                if (Number.isFinite(item.timeMs) && (!latest || item.timeMs > latest.timeMs)) {
                    latest = item;
                }
            });
        }

        const nowMs = Date.now();
        located.forEach((item) => {
            const { event, lat, lng, timeMs } = item;
            const kind = markerKind(timeMs, item === latest, nowMs);
            const marker = new google.maps.Marker({
                position: { lat, lng },
                map,
                title: `#${event.id ?? ""}`,
                icon: markerIcon(kind),
                // Keep the newest event on top; the canvas renderer would freeze its GIF.
                zIndex: kind === "latest" ? 3 : kind === "recent" ? 2 : 1,
                optimized: kind !== "latest",
            });
            marker.popupHtml = formatPopup(event);
            marker.addListener("click", () => {
                openMarker(marker);
                window.onMapEventSelected?.(event.id);
            });

            markers.push(marker);
            markersById.set(String(event.id), marker);
        });
    }

    function focusEventOnMap(eventId) {
        if (!ensureMap()) {
            return false;
        }
        const marker = markersById.get(String(eventId));
        if (!marker) {
            return false;
        }
        map.setCenter(marker.getPosition());
        map.setZoom(Math.max(map.getZoom(), FOCUS_ZOOM));
        openMarker(marker);
        return true;
    }

    function showMapUnavailable() {
        const mapElement = document.getElementById("map");
        if (!mapElement || map) {
            return;
        }
        mapElement.innerHTML = `
            <div class="events-map-unavailable">
                <i class="fa-solid fa-map-location-dot" aria-hidden="true"></i>
                <span>${escapeHtml(t("events.map.unavailable", "Map is unavailable."))}</span>
            </div>`;
    }

    // Called by the Google Maps script (callback=initEventsMap).
    window.initEventsMap = function () {
        if (!ensureMap()) {
            return;
        }
        if (pendingEvents) {
            const { events, options } = pendingEvents;
            pendingEvents = null;
            updateMapMarkers(events, options);
        }
    };

    // Google calls this when the API key is invalid or not allowed for this domain.
    window.gm_authFailure = function () {
        authFailed = true;
        map = null;
        markers = [];
        markersById.clear();
        showMapUnavailable();
    };

    window.updateMapMarkers = updateMapMarkers;
    window.focusEventOnMap = focusEventOnMap;
    window.ensureEventsMap = ensureMap;
    // Shared with the event details map so both look the same.
    window.EventMapStyle = { formatPopup, markerIcon, markerKind, originTimeMs };

    document.addEventListener("DOMContentLoaded", () => {
        const hasGoogleScript = document.querySelector('script[src*="maps.googleapis.com"]');
        if (!hasGoogleScript) {
            showMapUnavailable();
        }
    });
})();
