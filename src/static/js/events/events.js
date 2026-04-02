const eventsTableBody = document.getElementById("eventsTableBody");
const eventsStatus = document.getElementById("eventsStatus");
const addEventForm = document.getElementById("addEventForm");
const addEventSubmitBtn = document.getElementById("addEventSubmitBtn");
const addEventStatus = document.getElementById("addEventStatus");

function escapeHtml(value) {
  const div = document.createElement("div");
  div.textContent = value ?? "";
  return div.innerHTML;
}

function getApiKey() {
  let apiKey = window.localStorage.getItem("ies_api_key");
  if (!apiKey) {
    apiKey = window.prompt("შეიყვანე X-API-Key ივენთის დასამატებლად:");
    if (apiKey) {
      window.localStorage.setItem("ies_api_key", apiKey);
    }
  }
  return apiKey;
}

function renderEvents(events) {
  if (!Array.isArray(events) || events.length === 0) {
    eventsTableBody.innerHTML = "";
    eventsStatus.textContent = "ივენთები ვერ მოიძებნა.";
    return;
  }

  const sortedEvents = [...events].sort((a, b) => {
    const aTime = new Date(a.origin_time || 0).getTime();
    const bTime = new Date(b.origin_time || 0).getTime();
    return bTime - aTime;
  });

  eventsTableBody.innerHTML = sortedEvents
    .map(
      (event) => `
      <tr>
        <td>${escapeHtml(event.event_id)}</td>
        <td>${escapeHtml(event.seiscomp_oid)}</td>
        <td>${escapeHtml(event.origin_time)}</td>
        <td>${escapeHtml(event.ml)}</td>
        <td>${escapeHtml(event.depth)}</td>
        <td>${escapeHtml(event.latitude)}</td>
        <td>${escapeHtml(event.longitude)}</td>
        <td>${escapeHtml(event.region_ge || event.region_en || event.area || "-")}</td>
      </tr>
    `
    )
    .join("");

  eventsStatus.textContent = `ჩაიტვირთა ${sortedEvents.length} ივენთი.`;
}

async function loadEvents() {
  eventsStatus.textContent = "ივენთები იტვირთება...";

  try {
    const response = await fetch("/api/events", {
      method: "GET",
      headers: { accept: "application/json" },
    });
    const payload = await response.json();

    if (!response.ok) {
      eventsTableBody.innerHTML = "";
      eventsStatus.textContent = payload.error || "ივენთების ჩატვირთვა ვერ მოხერხდა.";
      return;
    }

    renderEvents(payload);
  } catch {
    eventsTableBody.innerHTML = "";
    eventsStatus.textContent = "მოთხოვნა ჩავარდა ივენთების ჩატვირთვისას.";
  }
}

async function createEvent(event) {
  event.preventDefault();

  const apiKey = getApiKey();
  if (!apiKey) {
    addEventStatus.textContent = "API key აუცილებელია ივენთის დასამატებლად.";
    addEventStatus.className = "small mt-3 text-danger";
    return;
  }

  const payload = {
    event_id: Number(document.getElementById("eventIdInput").value),
    seiscomp_oid: document.getElementById("seiscompOidInput").value.trim(),
    origin_time: document.getElementById("originTimeInput").value.trim(),
    origin_msec: document.getElementById("originMsecInput").value
      ? Number(document.getElementById("originMsecInput").value)
      : null,
    latitude: Number(document.getElementById("latitudeInput").value),
    longitude: Number(document.getElementById("longitudeInput").value),
    depth: Number(document.getElementById("depthInput").value),
    region_ge: document.getElementById("regionGeInput").value.trim() || null,
    region_en: document.getElementById("regionEnInput").value.trim() || null,
    area: document.getElementById("areaInput").value.trim() || null,
    ml: Number(document.getElementById("mlInput").value),
  };

  addEventSubmitBtn.disabled = true;
  addEventStatus.textContent = "ივენთის დამატება მიმდინარეობს...";
  addEventStatus.className = "small mt-3 text-muted";

  try {
    const response = await fetch("/api/events", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        accept: "application/json",
        "X-API-Key": apiKey,
      },
      body: JSON.stringify(payload),
    });
    const data = await response.json();

    if (!response.ok) {
      addEventStatus.textContent = data.error || "ივენთის დამატება ვერ მოხერხდა.";
      addEventStatus.className = "small mt-3 text-danger";
      return;
    }

    addEventStatus.textContent = data.message || "ივენთი წარმატებით დაემატა.";
    addEventStatus.className = "small mt-3 text-success";
    addEventForm.reset();
    await loadEvents();
  } catch {
    addEventStatus.textContent = "მოთხოვნა ჩავარდა ივენთის დამატებისას.";
    addEventStatus.className = "small mt-3 text-danger";
  } finally {
    addEventSubmitBtn.disabled = false;
  }
}

addEventForm.addEventListener("submit", createEvent);
loadEvents();
