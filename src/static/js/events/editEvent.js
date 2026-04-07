const editEventForm = document.getElementById("editEventForm");
const editEventSubmitBtn = document.getElementById("editEventSubmitBtn");
const editEventStatus = document.getElementById("editEventStatus");
const editEventModalElement = document.getElementById("editEventModal");
const editEventModal = editEventModalElement ? new bootstrap.Modal(editEventModalElement) : null;

function buildEditEventPayload() {
  return {
    event_id: Number(document.getElementById("editEventIdInput").value),
    seiscomp_oid: document.getElementById("editSeiscompOidInput").value.trim(),
    origin_time: document.getElementById("editOriginTimeInput").value.trim(),
    origin_msec: document.getElementById("editOriginMsecInput").value
      ? Number(document.getElementById("editOriginMsecInput").value)
      : null,
    latitude: Number(document.getElementById("editLatitudeInput").value),
    longitude: Number(document.getElementById("editLongitudeInput").value),
    depth: Number(document.getElementById("editDepthInput").value),
    region_ge: document.getElementById("editRegionGeInput").value.trim() || null,
    region_en: document.getElementById("editRegionEnInput").value.trim() || null,
    area: document.getElementById("editAreaInput").value.trim() || null,
    ml: Number(document.getElementById("editMlInput").value),
  };
}

window.openEditEventModal = function openEditEventModal(eventId) {
  const eventMap = window.eventsById;
  const event = eventMap?.get(String(eventId));
  if (!event || !editEventModal) {
    return;
  }

  document.getElementById("editEventIdInput").value = event.event_id ?? "";
  document.getElementById("editSeiscompOidInput").value = event.seiscomp_oid ?? "";
  document.getElementById("editOriginTimeInput").value = event.origin_time ?? "";
  document.getElementById("editOriginMsecInput").value = event.origin_msec ?? "";
  document.getElementById("editLatitudeInput").value = event.latitude ?? "";
  document.getElementById("editLongitudeInput").value = event.longitude ?? "";
  document.getElementById("editDepthInput").value = event.depth ?? "";
  document.getElementById("editMlInput").value = event.ml ?? "";
  document.getElementById("editRegionGeInput").value = event.region_ge ?? "";
  document.getElementById("editRegionEnInput").value = event.region_en ?? "";
  document.getElementById("editAreaInput").value = event.area ?? "";
  editEventStatus.textContent = "";
  editEventStatus.className = "small mt-3 text-muted";

  editEventModal.show();
};

async function submitEditEvent(event) {
  event.preventDefault();

  const apiKey = window.getApiKey ? window.getApiKey() : null;
  if (!apiKey) {
    const message = "API key აუცილებელია ივენთის რედაქტირებისთვის.";
    editEventStatus.textContent = message;
    editEventStatus.className = "small mt-3 text-danger";
    showAlert("alertPlaceholder", "danger", message);
    return;
  }

  const payload = buildEditEventPayload();
  editEventSubmitBtn.disabled = true;
  editEventStatus.textContent = "ივენთის განახლება მიმდინარეობს...";
  editEventStatus.className = "small mt-3 text-muted";

  try {
    const data = await makeApiRequest("/api/events", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        accept: "application/json",
        "X-API-Key": apiKey,
      },
      body: JSON.stringify(payload),
    });

    if (!data || data.error) {
      const message = data?.error || "ივენთის განახლება ვერ მოხერხდა.";
      editEventStatus.textContent = message;
      editEventStatus.className = "small mt-3 text-danger";
      showAlert("alertPlaceholder", "danger", message);
      return;
    }

    const message = data.message || "ივენთი წარმატებით განახლდა.";
    editEventStatus.textContent = message;
    editEventStatus.className = "small mt-3 text-success";
    showAlert("alertPlaceholder", "success", message);

    if (window.loadEvents) {
      await window.loadEvents();
    }
    closeModal("editEventModal");
  } catch {
    const message = "მოთხოვნა ჩავარდა ივენთის განახლებისას.";
    editEventStatus.textContent = message;
    editEventStatus.className = "small mt-3 text-danger";
    showAlert("alertPlaceholder", "danger", message);
  } finally {
    editEventSubmitBtn.disabled = false;
  }
}

if (editEventForm) {
  editEventForm.addEventListener("submit", submitEditEvent);
}
