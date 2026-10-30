/**
 * Calculated ShakeMap on the earthquake details tab.
 * Products are loaded through this app: /api/shakemap/product/<filename>?seiscomp_oid=
 */

const ShakeMap = window.ShakeMap || {
    map: null,
    infoWindow: null,
    epicenterMarker: null,
    currentLayers: {},
    activeBasemap: "satellite",
    legendEl: null,
    loadedOid: null,
    legendUrl: null,
  };
  window.ShakeMap = ShakeMap;
  
  const intColors_USGS = [
    "#FFFFFF",
    "#FFFFFF",
    "#B0E0FF",
    "#6EC0FF",
    "#00FF00",
    "#FFFF00",
    "#FFC800",
    "#FF7F00",
    "#FF0000",
    "#C00000",
    "#800080",
  ];
  
  const DATA_LAYER_KEYS = ["Intensity", "PGA", "PGV", "PSA 0.3s", "PSA 1.0s", "PSA 3.0s"];
  
  function formatUnit(unit) {
    if (!unit) {
      return "";
    }
    const value = String(unit).trim();
    if (!value || value.toLowerCase() === "mmi") {
      return "";
    }
    return value;
  }
  
  function shakemapText(key, fallback) {
    return window.I18n ? window.I18n.t(key, fallback) : fallback;
  }

  function getShakemapProductUrl(seiscompOid, filename) {
    const params = new URLSearchParams({ seiscomp_oid: seiscompOid });
    return `/api/shakemap/product/${encodeURIComponent(filename)}?${params}`;
  }

  function fetchProduct(seiscompOid, filename) {
    const headers = { Accept: "*/*" };
    const token = localStorage.getItem("access_token");
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }
    return fetch(getShakemapProductUrl(seiscompOid, filename), {
      credentials: "include",
      headers,
    });
  }
  
  function resolveEventCoords(event) {
    const lat = parseFloat(event.lat ?? event.latitude);
    const lon = parseFloat(event.lon ?? event.longitude);
    return { lat, lon };
  }
  
  function resolveSeiscompOid(event) {
    return String(event.seiscomp_oid || event.id || "").trim();
  }
  
  function isGoogleMapsReady() {
    return typeof google !== "undefined" && google.maps && typeof google.maps.Map === "function";
  }
  
  function clearShakeMapOverlays() {
    Object.values(ShakeMap.currentLayers || {}).forEach((layer) => {
      if (!layer) {
        return;
      }
      if (layer.type === "data" && layer.data) {
        layer.data.setMap(null);
      } else if (layer.type === "markers" && Array.isArray(layer.markers)) {
        layer.markers.forEach((marker) => marker.setMap(null));
      } else if (layer.type === "legend" && layer.el) {
        layer.el.remove();
      }
    });
    ShakeMap.currentLayers = {};
  
    if (ShakeMap.legendUrl) {
      URL.revokeObjectURL(ShakeMap.legendUrl);
      ShakeMap.legendUrl = null;
    }
    if (ShakeMap.epicenterMarker) {
      ShakeMap.epicenterMarker.setMap(null);
      ShakeMap.epicenterMarker = null;
    }
    if (ShakeMap.infoWindow) {
      ShakeMap.infoWindow.close();
    }
  }
  
  function openInfoWindow(position, html) {
    if (!ShakeMap.map) {
      return;
    }
    if (!ShakeMap.infoWindow) {
      ShakeMap.infoWindow = new google.maps.InfoWindow();
    }
    ShakeMap.infoWindow.setContent(html);
    ShakeMap.infoWindow.setPosition(position);
    ShakeMap.infoWindow.open({ map: ShakeMap.map });
  }
  
  function stationPopupHtml(feature) {
    const props = feature.properties || {};
    const code = props.code || props.id || "Unknown";
    const network = props.network || (props.name ? String(props.name).split(".")[0] : "N/A");
    const stationName = String(code).includes(".")
      ? String(code).split(".").slice(1).join(".")
      : code;
  
    const formatNumber = (val, decimals) => {
      return val !== null && val !== undefined && !Number.isNaN(Number(val))
        ? Number(val).toFixed(decimals)
        : "N/A";
    };
  
    return `
      <div style="font-family: Arial, sans-serif; font-size: 13px; line-height: 1.6;">
        <strong>Station:</strong> ${stationName}<br>
        <strong>Network:</strong> ${network}<br>
        <strong>Type:</strong> ${props.station_type || "N/A"}<br>
        <strong>Distance:</strong> ${formatNumber(props.distance, 3)} km<br>
        <strong>Intensity:</strong> ${formatNumber(props.intensity, 1)}<br>
        <strong>PGA:</strong> ${formatNumber(props.pga, 4)}<br>
        <strong>PGV:</strong> ${formatNumber(props.pgv, 4)}<br>
        <strong>Vs30:</strong> ${
          props.vs30 && !Number.isNaN(Number(props.vs30)) ? Math.round(props.vs30) : "N/A"
        } m/s
      </div>
    `;
  }
  
  function contourPopupHtml(layerName, feature) {
    const props = feature.properties || {};
    if (props.value == null) {
      return null;
    }
    let label = layerName;
    let unit = formatUnit(props.units || "");
    if (layerName.includes("Intensity")) {
      label = "Intensity";
      if (unit.toLowerCase() === "mmi") {
        unit = "";
      }
    }
    return `${label}: ${props.value} ${unit}`.trim();
  }
  
  function geoPointToLatLng(geometry) {
    if (!geometry || !geometry.coordinates) {
      return null;
    }
    // GeoJSON Point: [lon, lat]
    return { lat: Number(geometry.coordinates[1]), lng: Number(geometry.coordinates[0]) };
  }
  
  function styleContourDataLayer(dataLayer, fallbackColor) {
    dataLayer.setStyle((feature) => {
      const color = feature.getProperty("color") || fallbackColor;
      const weight = Number(feature.getProperty("weight")) || 2;
      return {
        strokeColor: color,
        strokeOpacity: 1,
        strokeWeight: weight,
        fillOpacity: 0,
        clickable: true,
      };
    });
  }
  
  /**
   * Create a Google Maps Data layer for contour GeoJSON.
   * visible=false keeps data loaded but not shown.
   */
  function createDataContourLayer(geojson, fallbackColor, layerName, visible) {
    const dataLayer = new google.maps.Data({ map: visible ? ShakeMap.map : null });
    dataLayer.addGeoJson(geojson);
    styleContourDataLayer(dataLayer, fallbackColor);
  
    dataLayer.addListener("click", (event) => {
      const props = {};
      event.feature.forEachProperty((value, key) => {
        props[key] = value;
      });
      const html = contourPopupHtml(layerName, { properties: props });
      if (html) {
        openInfoWindow(event.latLng, html);
      }
    });
  
    return { type: "data", data: dataLayer, visible };
  }
  
  function setLayerVisible(layer, visible) {
    if (!layer) {
      return;
    }
    layer.visible = visible;
    if (layer.type === "data" && layer.data) {
      layer.data.setMap(visible ? ShakeMap.map : null);
    } else if (layer.type === "markers" && Array.isArray(layer.markers)) {
      layer.markers.forEach((marker) => marker.setMap(visible ? ShakeMap.map : null));
    } else if (layer.type === "legend" && layer.el) {
      layer.el.style.display = visible ? "block" : "none";
    }
  }
  
  function appendLayerControl(layerList, name, inputType, groupName, checked, onChangeCall) {
    if (!layerList) {
      return;
    }
    const div = document.createElement("div");
    div.innerHTML = `
      <label>
        <input type="${inputType}" ${groupName ? `name="${groupName}"` : ""} ${
      checked ? "checked" : ""
    } onchange="${onChangeCall}">
        ${name}
      </label>
    `;
    layerList.appendChild(div);
  }
  
  function stationFillColor(feature) {
    const props = feature.properties || {};
    let stationColorIndex = 1;
    let useComplexLogic = false;
  
    if (props.mmi_from_pgm && Array.isArray(props.mmi_from_pgm)) {
      try {
        if (props.intensity < 5) {
          const result = props.mmi_from_pgm.find((obj) => obj.name === "pga");
          if (result) {
            stationColorIndex = Math.round(result.value);
            useComplexLogic = true;
          }
        } else {
          const result = props.mmi_from_pgm.find((obj) => obj.name === "pgv");
          if (result) {
            stationColorIndex = Math.round(result.value);
            useComplexLogic = true;
          }
        }
      } catch (err) {
        console.warn("Error in station color logic", err);
      }
    }
  
    if (!useComplexLogic) {
      stationColorIndex = Math.round(props.intensity || 1);
    }
    return intColors_USGS[stationColorIndex] || "#FFFFFF";
  }
  
  function triangleIcon(fillColor) {
    const svg = `
      <svg xmlns="http://www.w3.org/2000/svg" width="14" height="12" viewBox="0 0 14 12">
        <polygon points="7,0 14,12 0,12" fill="#000"/>
        <polygon points="7,2 13,12 1,12" fill="${fillColor}"/>
      </svg>
    `.trim();
    return {
      url: `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`,
      scaledSize: new google.maps.Size(14, 12),
      anchor: new google.maps.Point(7, 12),
    };
  }
  
  function circleIcon(fillColor) {
    const svg = `
      <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 12 12">
        <circle cx="6" cy="6" r="5" fill="${fillColor}" stroke="#000" stroke-width="1"/>
      </svg>
    `.trim();
    return {
      url: `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`,
      scaledSize: new google.maps.Size(12, 12),
      anchor: new google.maps.Point(6, 6),
    };
  }
  
  /**
   * @param {Object} event - { seiscomp_oid, latitude|lat, longitude|lon }
   * @param {Object} options
   */
  async function initShakeMapMap(event, options = {}) {
    const mapEl = document.getElementById(options.mapElementId || "shakemap-map");
    const layerList = document.getElementById(options.layerListId || "layer-list");
  
    if (!mapEl) {
      console.warn("ShakeMap map: container #shakemap-map missing");
      return;
    }
    if (!isGoogleMapsReady()) {
      console.warn("ShakeMap map: Google Maps API is not loaded");
      if (layerList) {
        layerList.innerHTML =
          '<div class="text-danger small">Google Maps API is not available. Check GOOGLE_MAPS_API_KEY.</div>';
      }
      return;
    }
  
    const seiscompOid = resolveSeiscompOid(event);
    const { lat, lon } = resolveEventCoords(event);
    if (!seiscompOid || Number.isNaN(lat) || Number.isNaN(lon)) {
      if (layerList) {
        layerList.innerHTML =
          '<div class="text-muted small">Event coordinates or SeisComP OID missing.</div>';
      }
      return;
    }
  
    if (ShakeMap.loadedOid === seiscompOid && ShakeMap.map) {
      google.maps.event.trigger(ShakeMap.map, "resize");
      return;
    }

    const selectedBasemap = ShakeMap.activeBasemap || "satellite";

    let view = { info: null, layers: {}, stations: null, rupture: null, has_legend: false };
    try {
      const params = new URLSearchParams({ seiscomp_oid: seiscompOid });
      view = await window.makeApiRequest(`/api/shakemap/view?${params}`);
    } catch (error) {
      if (layerList) {
        layerList.textContent =
          error.message ||
          shakemapText(
            "events.details.shakemap_empty",
            "ShakeMap has not been calculated for this event yet."
          );
      }
      return;
    }
  
    clearShakeMapOverlays();
  
    let bounds = new google.maps.LatLngBounds(
      { lat: lat - 0.5, lng: lon - 0.5 },
      { lat: lat + 0.5, lng: lon + 0.5 }
    );
    const mapInfo = view.info?.output?.map_information;
    if (mapInfo?.min && mapInfo?.max) {
      const minLat = parseFloat(mapInfo.min.latitude);
      const minLon = parseFloat(mapInfo.min.longitude);
      const maxLat = parseFloat(mapInfo.max.latitude);
      const maxLon = parseFloat(mapInfo.max.longitude);
      if (![minLat, minLon, maxLat, maxLon].some(Number.isNaN)) {
        bounds = new google.maps.LatLngBounds(
          { lat: minLat, lng: minLon },
          { lat: maxLat, lng: maxLon }
        );
      }
    }
  
    const mapTypeId =
      selectedBasemap === "street"
        ? google.maps.MapTypeId.ROADMAP
        : google.maps.MapTypeId.HYBRID;
  
    if (ShakeMap.map) {
      ShakeMap.map.setOptions({
        center: { lat, lng: lon },
        mapTypeId,
        streetViewControl: false,
        fullscreenControl: true,
        mapTypeControl: false,
      });
    } else {
      ShakeMap.map = new google.maps.Map(mapEl, {
        center: { lat, lng: lon },
        zoom: 8,
        mapTypeId,
        panControl: false,
        streetViewControl: false,
        mapTypeControl: false,
        zoomControl: true,
        fullscreenControl: true,
      });
    }
  
    ShakeMap.map.fitBounds(bounds);
    ShakeMap.infoWindow = new google.maps.InfoWindow();
  
    // Epicenter animated GIF
    ShakeMap.epicenterMarker = new google.maps.Marker({
      position: { lat, lng: lon },
      map: ShakeMap.map,
      title: "Epicenter",
      zIndex: 1000,
      optimized: false, // required for GIF animation in Google Maps markers
      icon: {
        url: "/static/images/earthquake_latest.gif",
        scaledSize: new google.maps.Size(40, 40),
        anchor: new google.maps.Point(20, 20),
      },
    });
    ShakeMap.epicenterMarker.addListener("click", () => {
      openInfoWindow({ lat, lng: lon }, "<strong>Epicenter</strong>");
    });
  
    if (layerList) {
      layerList.innerHTML = "";
    }
    ShakeMap.currentLayers = {};
  
    if (layerList) {
      const basemapDiv = document.createElement("div");
      basemapDiv.className = "shakemap-layer-group";
      basemapDiv.innerHTML = `
        <label class="d-block mb-2">
          <input type="radio" name="basemap" value="street" ${
            selectedBasemap === "street" ? "checked" : ""
          } onchange="switchBasemap('street')">
          Street
        </label>
        <label class="d-block mb-2">
          <input type="radio" name="basemap" value="satellite" ${
            selectedBasemap === "satellite" ? "checked" : ""
          } onchange="switchBasemap('satellite')">
          Satellite
        </label>
      `;
      layerList.appendChild(basemapDiv);
      layerList.appendChild(Object.assign(document.createElement("hr"), { className: "my-3" }));
    }
  
    const dataLayers = [
      { name: "Intensity", file: "cont_mi.json", color: "#ff0000" },
      { name: "PGA", file: "cont_pga.json", color: "#0000ff" },
      { name: "PGV", file: "cont_pgv.json", color: "#008000" },
      { name: "PSA 0.3s", file: "cont_psa0p3.json", color: "#ffa500" },
      { name: "PSA 1.0s", file: "cont_psa1p0.json", color: "#800080" },
      { name: "PSA 3.0s", file: "cont_psa3p0.json", color: "#a52a2a" },
    ];
  
    let firstLayer = true;
    dataLayers.forEach((item) => {
      const geojson = view.layers?.[item.name];
      if (!geojson) {
        return;
      }
      const checked = firstLayer;
      firstLayer = false;
      const layer = createDataContourLayer(geojson, item.color, item.name, checked);
      ShakeMap.currentLayers[item.name] = layer;
      appendLayerControl(
        layerList,
        item.name,
        "radio",
        "datalayer",
        checked,
        `switchDataLayer('${item.name}')`
      );
    });

    if (layerList && !DATA_LAYER_KEYS.some((name) => ShakeMap.currentLayers[name])) {
      const note = document.createElement("div");
      note.className = "text-muted";
      note.textContent = shakemapText(
        "events.details.shakemap_empty",
        "ShakeMap has not been calculated for this event yet."
      );
      layerList.appendChild(note);
    } else {
      ShakeMap.loadedOid = seiscompOid;
    }
  
    if (layerList) {
      layerList.appendChild(Object.assign(document.createElement("hr"), { className: "my-3" }));
    }
  
    // Stations
    try {
      if (view.stations) {
        const geojson = view.stations;
        const features = Array.isArray(geojson.features) ? geojson.features : [];
  
        const macroFeatures = features.filter((f) => f.properties?.station_type === "macroseismic");
        const seismicFeatures = features.filter((f) => f.properties?.station_type !== "macroseismic");
  
        if (macroFeatures.length > 0) {
          const autoEnable = options.enableMacroseismic === true;
          const markers = macroFeatures
            .map((feature) => {
              const pos = geoPointToLatLng(feature.geometry);
              if (!pos || Number.isNaN(pos.lat) || Number.isNaN(pos.lng)) {
                return null;
              }
              const idx = Math.round(feature.properties?.intensity || 0);
              const color = intColors_USGS[idx] || "black";
              const marker = new google.maps.Marker({
                position: pos,
                map: autoEnable ? ShakeMap.map : null,
                icon: circleIcon(color),
                title: feature.properties?.code || "Macroseismic",
              });
              marker.addListener("click", () => openInfoWindow(pos, stationPopupHtml(feature)));
              return marker;
            })
            .filter(Boolean);
  
          ShakeMap.currentLayers.Macroseismic = {
            type: "markers",
            markers,
            visible: autoEnable,
          };
          appendLayerControl(
            layerList,
            "Show Reported Intensity",
            "checkbox",
            null,
            autoEnable,
            "toggleLayer('Macroseismic')"
          );
        }
  
        if (seismicFeatures.length > 0) {
          const markers = seismicFeatures
            .map((feature) => {
              const pos = geoPointToLatLng(feature.geometry);
              if (!pos || Number.isNaN(pos.lat) || Number.isNaN(pos.lng)) {
                return null;
              }
              const fill = stationFillColor(feature);
              const marker = new google.maps.Marker({
                position: pos,
                map: null,
                icon: triangleIcon(fill),
                title: feature.properties?.code || "Station",
              });
              marker.addListener("click", () => openInfoWindow(pos, stationPopupHtml(feature)));
              return marker;
            })
            .filter(Boolean);
  
          ShakeMap.currentLayers.Stations = { type: "markers", markers, visible: false };
          appendLayerControl(
            layerList,
            "Show Stations",
            "checkbox",
            null,
            false,
            "toggleLayer('Stations')"
          );
        }
      }
    } catch (e) {
      console.warn("Failed to draw stations", e);
    }
  
    // Fault / rupture
    try {
      if (view.rupture) {
        const ruptureJson = view.rupture;
        let isValidFault = false;
        if (ruptureJson.features && ruptureJson.features.length > 0) {
          const geometry = ruptureJson.features[0].geometry;
          if (geometry?.coordinates && Array.isArray(geometry.coordinates)) {
            if (Array.isArray(geometry.coordinates[0])) {
              isValidFault = true;
            }
          }
        }
        if (isValidFault) {
          const dataLayer = new google.maps.Data({ map: null });
          dataLayer.addGeoJson(ruptureJson);
          dataLayer.setStyle({
            strokeColor: "#000000",
            strokeWeight: 3,
            strokeOpacity: 1,
            fillOpacity: 0,
          });
          ShakeMap.currentLayers.Fault = { type: "data", data: dataLayer, visible: false };
          appendLayerControl(layerList, "Show fault", "checkbox", null, false, "toggleLayer('Fault')");
        }
      }
    } catch (e) {
      console.warn("Failed to draw rupture.json", e);
    }
  
    // Legend image overlay. Requested only when ShakeMap has the file.
    let legendExists = false;
    try {
      if (view.has_legend) {
        const legendRes = await fetchProduct(seiscompOid, "mmi_legend.png");
        if (legendRes.ok) {
          ShakeMap.legendUrl = URL.createObjectURL(await legendRes.blob());
          const legendEl = document.createElement("div");
          legendEl.className = "shakemap-gmap-legend";
          legendEl.innerHTML = `<img src="${ShakeMap.legendUrl}" alt="MMI Legend" class="shakemap-legend-img">`;
          mapEl.style.position = mapEl.style.position || "relative";
          mapEl.appendChild(legendEl);

          ShakeMap.currentLayers.Legend = { type: "legend", el: legendEl, visible: true };
          legendExists = true;
        }
      }
    } catch (e) {
      console.warn("Failed to load legend", e);
    }

    if (legendExists) {
      appendLayerControl(
        layerList,
        "Show Legend",
        "checkbox",
        null,
        true,
        "toggleLayer('Legend')"
      );
    }
  
    // Trigger resize after tab layout
    setTimeout(() => {
      if (ShakeMap.map) {
        google.maps.event.trigger(ShakeMap.map, "resize");
        ShakeMap.map.fitBounds(bounds);
      }
    }, 150);
  }
  
  window.switchDataLayer = function (selectedName) {
    DATA_LAYER_KEYS.forEach((name) => {
      const layer = ShakeMap.currentLayers[name];
      if (!layer) {
        return;
      }
      setLayerVisible(layer, name === selectedName);
    });
  };
  
  window.toggleLayer = function (name) {
    const layer = ShakeMap.currentLayers[name];
    if (!layer) {
      return;
    }
    setLayerVisible(layer, !layer.visible);
  };
  
  window.switchBasemap = function (basemapType) {
    ShakeMap.activeBasemap = basemapType;
    if (!ShakeMap.map || !isGoogleMapsReady()) {
      return;
    }
    ShakeMap.map.setMapTypeId(
      basemapType === "street" ? google.maps.MapTypeId.ROADMAP : google.maps.MapTypeId.HYBRID
    );
  };
  
  window.initShakeMapMap = initShakeMapMap;
  window.getShakemapProductUrl = getShakemapProductUrl;
  window.isGoogleMapsReady = isGoogleMapsReady;

  let pendingShakeEvent = null;

  function showShakeMapStatus(key, fallback) {
    const layerList = document.getElementById("shakemap-layer-list");
    if (layerList) {
      layerList.textContent = shakemapText(key, fallback);
    }
  }

  function refreshShakeMap() {
    const pane = document.getElementById("panel-shakemap");
    if (!pane || !pane.classList.contains("active")) {
      return;
    }
    const event = pendingShakeEvent;
    if (!event) {
      return;
    }
    if (!String(event.seiscomp_oid || "").trim()) {
      showShakeMapStatus(
        "events.details.shakemap_no_oid",
        "This earthquake has no SeisComP id, so ShakeMap cannot be loaded."
      );
      return;
    }
    const lat = parseFloat(event.latitude);
    const lon = parseFloat(event.longitude);
    if (Number.isNaN(lat) || Number.isNaN(lon)) {
      showShakeMapStatus("events.details.map_unavailable", "Map coordinates are unavailable.");
      return;
    }
    if (!document.querySelector('script[src*="maps.googleapis.com"]')) {
      showShakeMapStatus("events.map.unavailable", "Map is unavailable.");
      return;
    }
    if (!isGoogleMapsReady()) {
      return;
    }
    initShakeMapMap(event, {
      mapElementId: "shakemap-map",
      layerListId: "shakemap-layer-list",
    });
  }

  window.renderEventShakeMap = (event) => {
    if (pendingShakeEvent && pendingShakeEvent.seiscomp_oid !== event?.seiscomp_oid) {
      ShakeMap.loadedOid = null;
    }
    pendingShakeEvent = event;
    refreshShakeMap();
  };
  window.refreshShakeMap = refreshShakeMap;

  // Called by the Google Maps script (callback=initEventDetailMap).
  window.initEventDetailMap = () => {
    refreshShakeMap();
  };

  const previousGmAuthFailure = window.gm_authFailure;
  window.gm_authFailure = () => {
    previousGmAuthFailure?.();
    showShakeMapStatus("events.map.unavailable", "Map is unavailable.");
  };