const addEventForm = document.getElementById("addEventForm");
const addEventSubmitBtn = document.getElementById("addEventSubmitBtn");
const addEventStatus = document.getElementById("addEventStatus");

function buildCreateEventPayload() {
  return {
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
}

async function createEvent(event) {
  event.preventDefault();

  const payload = buildCreateEventPayload();
  addEventSubmitBtn.disabled = true;
  addEventStatus.textContent = "ივენთის დამატება მიმდინარეობს...";
  addEventStatus.className = "small mt-3 text-muted";

  try {
    const data = await window.makeApiRequest("/api/events", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        accept: "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!data || data.error) {
      const message = data?.error || "ივენთის დამატება ვერ მოხერხდა.";
      addEventStatus.textContent = message;
      addEventStatus.className = "small mt-3 text-danger";
      showAlert("alertPlaceholder", "danger", message);
      return;
    }

    const message = data.message || "ივენთი წარმატებით დაემატა.";
    addEventStatus.textContent = message;
    addEventStatus.className = "small mt-3 text-success";
    showAlert("alertPlaceholder", "success", message);
    addEventForm.reset();
    if (window.loadEvents) {
      await window.loadEvents();
    }
  } catch {
    const message = "მოთხოვნა ჩავარდა ივენთის დამატებისას.";
    addEventStatus.textContent = message;
    addEventStatus.className = "small mt-3 text-danger";
    showAlert("alertPlaceholder", "danger", message);
  } finally {
    addEventSubmitBtn.disabled = false;
  }
}

if (addEventForm) {
  addEventForm.addEventListener("submit", createEvent);
}
