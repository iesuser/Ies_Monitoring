const eventsTableBody = document.getElementById("eventsTableBody");
const eventsStatus = document.getElementById("eventsStatus");
const eventsById = new Map();

function escapeHtml(value) {
  const div = document.createElement("div");
  div.textContent = value ?? "";
  return div.innerHTML;
}

function getApiKey() {
  let apiKey = window.localStorage.getItem("ies_api_key");
  if (!apiKey) {
    apiKey = window.prompt("შეიყვანე X-API-Key:");
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
  eventsById.clear();
  sortedEvents.forEach((event) => eventsById.set(String(event.event_id), event));
  window.eventsById = eventsById;

  eventsTableBody.innerHTML = sortedEvents
    .map(
      (event) => `
      <tr>
        <td>
          <div class="d-flex align-items-center gap-1">
            <button
              type="button"
              class="btn btn-sm btn-outline-secondary edit-event-btn d-inline-flex align-items-center justify-content-center"
              onclick="openEditEventModal('${escapeHtml(event.event_id)}')"
              title="ივენთის რედაქტირება"
              aria-label="ივენთის რედაქტირება"
            >
              <img
                src="/static/img/pen-solid.svg"
                alt="რედაქტირება"
                style="width: 14px; height: 14px;"
              >
            </button>
            <button
              type="button"
              class="btn btn-sm btn-outline-danger d-inline-flex align-items-center justify-content-center"
              onclick="deleteEvent('${escapeHtml(event.event_id)}')"
              title="ივენთის წაშლა"
              aria-label="ივენთის წაშლა"
            >
              <img
                src="/static/img/trash-solid.svg"
                alt="წაშლა"
                style="width: 14px; height: 14px;"
              >
            </button>
          </div>
        </td>
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

  eventsStatus.textContent = `ჩაიტვირთა ${sortedEvents.length} მიწისძვრა.`;
}

function renderEventsAndMap(events) {
  renderEvents(events);
  if (typeof window.updateMapMarkers === "function") {
    window.updateMapMarkers(Array.isArray(events) ? events : []);
  }
}

async function loadEvents() {
  eventsStatus.textContent = "მიწისძვრები იტვირთება...";

  try {
    const response = await fetch("/api/events", {
      method: "GET",
      headers: { accept: "application/json" },
    });
    const payload = await response.json();

    if (!response.ok) {
      eventsTableBody.innerHTML = "";
      eventsStatus.textContent = payload.error || "მიწისძვრების ჩატვირთვა ვერ მოხერხდა.";
      return;
    }

    renderEventsAndMap(Array.isArray(payload) ? payload : []);
  } catch {
    eventsTableBody.innerHTML = "";
    eventsStatus.textContent = "მოთხოვნა ჩავარდა მიწისძვრების ჩატვირთვისას.";
  }
}
window.escapeHtml = escapeHtml;
window.getApiKey = getApiKey;
window.renderEvents = renderEvents;
window.renderEventsAndMap = renderEventsAndMap;
window.loadEvents = loadEvents;

document.addEventListener("DOMContentLoaded", loadEvents);
