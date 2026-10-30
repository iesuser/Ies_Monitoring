let editEventModal = null;

const EDIT_EVENT_ALERT_ID = "editEventAlertPlaceholder";

function t(key, fallback) {
    const i18n = window.I18n;
    return i18n ? i18n.t(key, fallback) : fallback;
}

function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
}

function ensureEditEventModal() {
    if (editEventModal) {
        return editEventModal;
    }
    const modalElement = document.getElementById("editEventModal");
    if (modalElement && window.bootstrap?.Modal) {
        editEventModal = bootstrap.Modal.getOrCreateInstance(modalElement);
    }
    return editEventModal;
}

function clearEditEventAlert() {
    const container = document.getElementById(EDIT_EVENT_ALERT_ID);
    if (container) {
        container.innerHTML = "";
    }
}

function toOriginTimeInputValue(isoValue) {
    if (window.formatOriginTime) {
        const formatted = window.formatOriginTime(isoValue);
        return formatted === "-" ? "" : formatted;
    }
    if (!isoValue) {
        return "";
    }
    const date = new Date(isoValue);
    if (Number.isNaN(date.getTime())) {
        return "";
    }
    const pad = (value) => String(value).padStart(2, "0");
    return (
        `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T` +
        `${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
    );
}

function fromOriginTimeInput(value) {
    if (window.parseOriginTimeInput) {
        return window.parseOriginTimeInput(value);
    }
    const raw = (value || "").trim();
    if (!raw) {
        return null;
    }
    const date = new Date(raw);
    if (Number.isNaN(date.getTime())) {
        return null;
    }
    return date.toISOString();
}

function renderMagnitudesSummary(magnitudes) {
    const container = document.getElementById("editEventMagnitudes");
    if (!container) {
        return;
    }
    const list = Array.isArray(magnitudes) ? magnitudes : [];
    if (!list.length) {
        container.innerHTML = `<span class="text-muted small">${escapeHtml(
            t("events.edit.magnitudes_empty", "No magnitudes recorded.")
        )}</span>`;
        return;
    }
    container.innerHTML = list
        .map((item) => {
            const code = item.magnitude?.code || "?";
            const value =
                item.value === null || item.value === undefined ? "" : Number(item.value);
            return `
        <div class="d-flex align-items-center gap-2" data-magnitude-id="${escapeHtml(item.id)}">
            <span class="badge text-bg-light border font-monospace">${escapeHtml(code)}</span>
            <input
                type="number"
                class="form-control form-control-sm"
                step="0.1"
                value="${escapeHtml(value)}"
                data-magnitude-value-for="${escapeHtml(item.id)}"
            >
            <button
                type="button"
                class="btn btn-sm btn-outline-secondary"
                data-magnitude-save="${escapeHtml(item.id)}"
                data-i18n="events.edit.magnitude_save"
            >
                Save
            </button>
            <button
                type="button"
                class="btn btn-sm btn-outline-danger"
                data-magnitude-delete="${escapeHtml(item.id)}"
                data-i18n="events.edit.magnitude_delete"
            >
                Delete
            </button>
        </div>
    `;
        })
        .join("");

    window.I18n?.applyTranslations?.();
}

let editMagnitudeTypesLoaded = false;

async function loadEditMagnitudeTypes() {
    const select = document.getElementById("editEventMagnitudeCode");
    if (!select || editMagnitudeTypesLoaded) {
        return;
    }

    try {
        const data = await window.makeApiRequest("/api/seismic_events/magnitude_types", {
            method: "GET",
        });
        (Array.isArray(data.items) ? data.items : []).forEach((item) => {
            const option = document.createElement("option");
            option.value = item.code;
            option.textContent = item.code;
            if (item.description) {
                option.title = item.description;
            }
            select.appendChild(option);
        });
        editMagnitudeTypesLoaded = true;
    } catch (error) {
        window.showAlert(
            EDIT_EVENT_ALERT_ID,
            "warning",
            error.message ||
                t("events.create.magnitude_types_error", "Failed to load magnitude types.")
        );
    }
}

async function refreshEventMagnitudes(eventId) {
    const event = await window.makeApiRequest(`/api/seismic_events/event_id=${eventId}`, {
        method: "GET",
    });
    renderMagnitudesSummary(event.magnitudes);
    window.onEventUpdated?.(event);
}

async function addEventMagnitude() {
    const eventId = document.getElementById("editEventId")?.value;
    const code = document.getElementById("editEventMagnitudeCode")?.value || "";
    const rawValue = document.getElementById("editEventMagnitudeValue")?.value ?? "";

    if (!eventId) {
        return;
    }

    if (!code || rawValue === "") {
        window.showAlert(
            EDIT_EVENT_ALERT_ID,
            "danger",
            t(
                "events.create.magnitude_incomplete",
                "Select both a magnitude type and its value, or leave both empty."
            )
        );
        return;
    }

    const addButton = document.getElementById("editEventMagnitudeAdd");
    addButton.disabled = true;
    clearEditEventAlert();

    try {
        await window.makeApiRequest(`/api/seismic_events/${eventId}/magnitudes`, {
            method: "POST",
            body: JSON.stringify({ value: Number(rawValue), magnitude_code: code }),
        });
        document.getElementById("editEventMagnitudeCode").value = "";
        document.getElementById("editEventMagnitudeValue").value = "";
        await refreshEventMagnitudes(eventId);
    } catch (error) {
        window.showAlert(
            EDIT_EVENT_ALERT_ID,
            "danger",
            error.message || t("events.edit.magnitude_add_error", "Failed to add magnitude.")
        );
    } finally {
        addButton.disabled = false;
    }
}

async function saveEventMagnitude(eventMagnitudeId) {
    const eventId = document.getElementById("editEventId")?.value;
    const input = document.querySelector(
        `[data-magnitude-value-for="${eventMagnitudeId}"]`
    );
    const rawValue = input?.value ?? "";

    if (rawValue === "") {
        window.showAlert(
            EDIT_EVENT_ALERT_ID,
            "danger",
            t("events.error.validation", "Please fill in all required fields.")
        );
        return;
    }

    clearEditEventAlert();

    try {
        await window.makeApiRequest(`/api/seismic_events/magnitudes/${eventMagnitudeId}`, {
            method: "PUT",
            body: JSON.stringify({ value: Number(rawValue) }),
        });
        await refreshEventMagnitudes(eventId);
    } catch (error) {
        window.showAlert(
            EDIT_EVENT_ALERT_ID,
            "danger",
            error.message ||
                t("events.edit.magnitude_update_error", "Failed to update magnitude.")
        );
    }
}

async function deleteEventMagnitude(eventMagnitudeId) {
    const eventId = document.getElementById("editEventId")?.value;

    const confirmed = await window.confirmDelete({
        message: t(
            "events.edit.magnitude_delete_confirm",
            "Are you sure you want to delete this magnitude?"
        ),
    });
    if (!confirmed) {
        return;
    }

    clearEditEventAlert();

    try {
        await window.makeApiRequest(`/api/seismic_events/magnitudes/${eventMagnitudeId}`, {
            method: "DELETE",
        });
        await refreshEventMagnitudes(eventId);
    } catch (error) {
        window.showAlert(
            EDIT_EVENT_ALERT_ID,
            "danger",
            error.message ||
                t("events.edit.magnitude_delete_error", "Failed to delete magnitude.")
        );
    }
}

let editEventHasBeachball = false;

function readOptionalNumber(id) {
    const raw = document.getElementById(id)?.value;
    if (raw === null || raw === undefined || raw === "") {
        return null;
    }
    const value = Number(raw);
    return Number.isNaN(value) ? null : value;
}

function setBeachballDeleteEnabled(enabled) {
    const deleteButton = document.getElementById("editEventBeachballDelete");
    if (deleteButton) {
        deleteButton.disabled = !enabled;
    }
}

function fillBeachballForm(beachball) {
    editEventHasBeachball = Boolean(beachball);
    document.getElementById("editEventBeachballStrike").value =
        beachball?.strike === null || beachball?.strike === undefined ? "" : beachball.strike;
    document.getElementById("editEventBeachballDip").value =
        beachball?.dip === null || beachball?.dip === undefined ? "" : beachball.dip;
    document.getElementById("editEventBeachballRake").value =
        beachball?.rake === null || beachball?.rake === undefined ? "" : beachball.rake;

    const pathEl = document.getElementById("editEventBeachballPath");
    if (pathEl) {
        pathEl.textContent = beachball?.beachball_path || "";
    }
    setBeachballDeleteEnabled(editEventHasBeachball);
}

function readBeachballPayload() {
    const payload = {};
    const strike = readOptionalNumber("editEventBeachballStrike");
    const dip = readOptionalNumber("editEventBeachballDip");
    const rake = readOptionalNumber("editEventBeachballRake");

    if (strike !== null) {
        payload.strike = strike;
    }
    if (dip !== null) {
        payload.dip = dip;
    }
    if (rake !== null) {
        payload.rake = rake;
    }
    return payload;
}

function isBeachballMechanismIncomplete(payload) {
    const filledCount = ["strike", "dip", "rake"].filter(
        (key) => payload?.[key] !== null && payload?.[key] !== undefined
    ).length;
    return filledCount > 0 && filledCount < 3;
}

function isBeachballPayloadEmpty(payload) {
    return Object.keys(payload).length === 0;
}

async function syncEventBeachball(eventId) {
    const payload = readBeachballPayload();
    if (isBeachballPayloadEmpty(payload)) {
        return;
    }

    if (editEventHasBeachball) {
        await window.makeApiRequest(`/api/seismic_events/${eventId}/beachball`, {
            method: "PUT",
            body: JSON.stringify(payload),
        });
    } else {
        await window.makeApiRequest(`/api/seismic_events/${eventId}/beachball`, {
            method: "POST",
            body: JSON.stringify(payload),
        });
        editEventHasBeachball = true;
    }
}

async function deleteEventBeachball() {
    const eventId = document.getElementById("editEventId")?.value;
    if (!eventId || !editEventHasBeachball) {
        return;
    }

    const confirmed = await window.confirmDelete({
        message: t(
            "events.edit.beachball_delete_confirm",
            "Are you sure you want to delete this beachball?"
        ),
    });
    if (!confirmed) {
        return;
    }

    const deleteButton = document.getElementById("editEventBeachballDelete");
    deleteButton.disabled = true;
    clearEditEventAlert();

    try {
        await window.makeApiRequest(`/api/seismic_events/${eventId}/beachball`, {
            method: "DELETE",
        });
        fillBeachballForm(null);
        const event = await window.makeApiRequest(`/api/seismic_events/event_id=${eventId}`, {
            method: "GET",
        });
        window.onEventUpdated?.(event);
        window.showAlert(
            EDIT_EVENT_ALERT_ID,
            "success",
            t("events.edit.beachball_delete_success", "Beachball deleted successfully.")
        );
    } catch (error) {
        window.showAlert(
            EDIT_EVENT_ALERT_ID,
            "danger",
            error.message ||
                t("events.edit.beachball_delete_error", "Failed to delete beachball.")
        );
        setBeachballDeleteEnabled(true);
    }
}

function setAreaValue(area) {
    const select = document.getElementById("editEventArea");
    if (!select) {
        return;
    }

    const isKnown = [...select.options].some((option) => option.value === area);
    if (!isKnown && area) {
        // Keep legacy free-text areas selectable so editing does not silently drop them.
        const option = document.createElement("option");
        option.value = area;
        option.textContent = area;
        select.appendChild(option);
    }

    select.value = area;
}

function fillEventForm(event) {
    document.getElementById("editEventId").value = event.id || "";
    document.getElementById("editEventIsPublished").value = event.is_published ? "1" : "0";
    document.getElementById("editEventOriginTime").value = toOriginTimeInputValue(
        event.origin_time
    );
    document.getElementById("editEventDepth").value =
        event.depth === null || event.depth === undefined ? "" : event.depth;
    document.getElementById("editEventLatitude").value =
        event.latitude === null || event.latitude === undefined ? "" : event.latitude;
    document.getElementById("editEventLongitude").value =
        event.longitude === null || event.longitude === undefined ? "" : event.longitude;
    document.getElementById("editEventLocationGe").value = event.location_ge || "";
    document.getElementById("editEventLocationEn").value = event.location_en || "";
    setAreaValue(event.area || "");
    document.getElementById("editEventIesdataId").value = event.iesdata_id ?? "";
    document.getElementById("editEventSeiscompOid").value = event.seiscomp_oid || "";
    renderMagnitudesSummary(event.magnitudes);
    fillBeachballForm(event.beachball);
}

async function openEditEventModal(eventId) {
    const modal = ensureEditEventModal();
    if (!modal) {
        window.showAlert?.(
            "alertPlaceholder",
            "danger",
            t("events.error.load_detail", "Failed to load earthquake details.")
        );
        return;
    }

    clearEditEventAlert();

    try {
        const event = await window.makeApiRequest(`/api/seismic_events/event_id=${eventId}`, {
            method: "GET",
        });
        fillEventForm(event);
        modal.show();
        await loadEditMagnitudeTypes();
    } catch (error) {
        window.showAlert(
            "alertPlaceholder",
            "danger",
            error.message || t("events.error.load_detail", "Failed to load earthquake details.")
        );
    }
}

async function submitEditEventForm(formEvent) {
    formEvent.preventDefault();

    const eventId = document.getElementById("editEventId").value;
    const originTimeLocal = document.getElementById("editEventOriginTime").value;
    const latitude = document.getElementById("editEventLatitude").value;
    const longitude = document.getElementById("editEventLongitude").value;
    const depth = document.getElementById("editEventDepth").value;
    const submitButton = document.getElementById("editEventSubmit");

    const origin_time = fromOriginTimeInput(originTimeLocal);
    if (!eventId || !origin_time || depth === "" || latitude === "" || longitude === "") {
        window.showAlert(
            EDIT_EVENT_ALERT_ID,
            "danger",
            t("events.error.validation", "Please fill in all required fields.")
        );
        return;
    }

    const iesdataIdText = document.getElementById("editEventIesdataId").value.trim();
    const iesdataId = iesdataIdText ? Number(iesdataIdText) : null;
    if (iesdataIdText && (!/^\d+$/.test(iesdataIdText) || iesdataId < 1)) {
        window.showAlert(
            EDIT_EVENT_ALERT_ID,
            "danger",
            t("events.error.iesdata_id_invalid", "IES data ID must be a positive integer.")
        );
        return;
    }

    const beachballPayload = readBeachballPayload();
    if (isBeachballMechanismIncomplete(beachballPayload)) {
        window.showAlert(
            EDIT_EVENT_ALERT_ID,
            "warning",
            t(
                "events.edit.beachball_incomplete",
                "strike, dip, and rake must all be provided together (or omit all three)."
            )
        );
        return;
    }

    submitButton.disabled = true;
    clearEditEventAlert();

    try {
        const payload = {
            origin_time,
            latitude: Number(latitude),
            longitude: Number(longitude),
            depth: Number(depth),
            location_ge: document.getElementById("editEventLocationGe").value.trim() || null,
            location_en: document.getElementById("editEventLocationEn").value.trim() || null,
            area: document.getElementById("editEventArea").value.trim() || null,
            iesdata_id: iesdataId,
            seiscomp_oid: document.getElementById("editEventSeiscompOid").value.trim() || null,
        };

        const data = await window.makeApiRequest(`/api/seismic_events/event_id=${eventId}`, {
            method: "PUT",
            body: JSON.stringify(payload),
        });

        let beachballWarning = null;
        try {
            await syncEventBeachball(eventId);
        } catch (beachballError) {
            beachballWarning =
                beachballError.message ||
                t(
                    "events.edit.beachball_warning",
                    "Event updated, but the beachball could not be saved."
                );
        }

        const refreshed = await window.makeApiRequest(`/api/seismic_events/event_id=${eventId}`, {
            method: "GET",
        });
        window.onEventUpdated?.(refreshed);
        ensureEditEventModal()?.hide();

        if (beachballWarning) {
            window.showAlert("alertPlaceholder", "warning", beachballWarning);
        } else {
            window.showAlert(
                "alertPlaceholder",
                "success",
                data.message || t("events.edit.success", "Earthquake updated successfully.")
            );
        }
    } catch (error) {
        window.showAlert(
            EDIT_EVENT_ALERT_ID,
            "danger",
            error.message || t("events.error.update", "Failed to update earthquake.")
        );
    } finally {
        submitButton.disabled = false;
    }
}

async function deleteEventFromModal() {
    const eventId = document.getElementById("editEventId").value;
    if (!eventId) {
        return;
    }

    if (document.getElementById("editEventIsPublished")?.value === "1") {
        window.showAlert(
            EDIT_EVENT_ALERT_ID,
            "warning",
            t(
                "events.delete.published_blocked",
                "This earthquake is published. Unpublish it first, then delete it."
            )
        );
        return;
    }

    const confirmed = await window.confirmDelete({
        message: t(
            "events.delete.confirm",
            "Are you sure you want to delete this earthquake?"
        ),
    });
    if (!confirmed) {
        return;
    }

    const deleteButton = document.getElementById("editEventDelete");
    deleteButton.disabled = true;

    try {
        const data = await window.makeApiRequest(`/api/seismic_events/event_id=${eventId}`, {
            method: "DELETE",
        });
        window.onEventDeleted?.(eventId);
        window.closeModal("editEventModal");
        window.showAlert(
            "alertPlaceholder",
            "success",
            data.message || t("events.delete.success", "Earthquake deleted successfully.")
        );
    } catch (error) {
        window.showAlert(
            EDIT_EVENT_ALERT_ID,
            error.code === "conflict" ? "warning" : "danger",
            error.message || t("events.error.delete", "Failed to delete earthquake.")
        );
    } finally {
        deleteButton.disabled = false;
    }
}

window.openEditEventModal = openEditEventModal;

document.addEventListener("DOMContentLoaded", () => {
    ensureEditEventModal();
    document
        .getElementById("editEventForm")
        ?.addEventListener("submit", submitEditEventForm);
    document
        .getElementById("editEventDelete")
        ?.addEventListener("click", deleteEventFromModal);
    document
        .getElementById("editEventMagnitudeAdd")
        ?.addEventListener("click", addEventMagnitude);
    document
        .getElementById("editEventBeachballDelete")
        ?.addEventListener("click", deleteEventBeachball);

    document.getElementById("editEventMagnitudes")?.addEventListener("click", (event) => {
        const saveButton = event.target.closest("[data-magnitude-save]");
        if (saveButton) {
            saveEventMagnitude(saveButton.dataset.magnitudeSave);
            return;
        }

        const deleteButton = event.target.closest("[data-magnitude-delete]");
        if (deleteButton) {
            deleteEventMagnitude(deleteButton.dataset.magnitudeDelete);
        }
    });
});
