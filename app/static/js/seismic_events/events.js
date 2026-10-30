const eventsTableBody = document.getElementById("eventsTableBody");
const eventsStatus = document.getElementById("eventsStatus");
const eventsActionHeader = document.getElementById("eventsActionHeader");
const eventsById = new Map();
const getEventKey = (event) => String(event?.id ?? "");

let allEvents = [];
let canViewEvents = false;
let canManageEvents = false;

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

function getEventMagnitude(event) {
    const list = (Array.isArray(event?.magnitudes) ? event.magnitudes : []).filter(
        (item) => item.value !== null && item.value !== undefined
    );
    if (!list.length) {
        return null;
    }

    // ML always wins; otherwise fall back to the first recorded magnitude.
    const preferred =
        list.find((item) => (item.magnitude?.code || "").toUpperCase() === "ML") || list[0];

    return {
        value: Number(preferred.value),
        code: preferred.magnitude?.code || "",
    };
}

function getEventMl(event) {
    return getEventMagnitude(event)?.value ?? null;
}

function preferredLocation(event) {
    const lang = window.I18n?.getLanguage?.() || "en";
    if (lang === "ka") {
        return event.location_ge || "-";
    }
    return event.location_en || "-";
}

function pad2(n) {
    return String(n).padStart(2, "0");
}

function toNaiveIsoString(year, month, day, hour = 0, minute = 0, second = 0) {
    return (
        `${year}-${pad2(month)}-${pad2(day)}T` +
        `${pad2(hour)}:${pad2(minute)}:${pad2(second)}`
    );
}

function formatOriginTime(value) {
    if (!value) {
        return "-";
    }

    const raw = String(value).trim();
    const isoMatch = raw.match(
        /^(\d{4})-(\d{2})-(\d{2})[T\s](\d{2}):(\d{2})(?::(\d{2}))?/
    );
    if (isoMatch) {
        return toNaiveIsoString(
            Number(isoMatch[1]),
            Number(isoMatch[2]),
            Number(isoMatch[3]),
            Number(isoMatch[4]),
            Number(isoMatch[5]),
            Number(isoMatch[6] ?? 0)
        );
    }

    const date = new Date(raw);
    if (Number.isNaN(date.getTime())) {
        return raw;
    }
    return toNaiveIsoString(
        date.getFullYear(),
        date.getMonth() + 1,
        date.getDate(),
        date.getHours(),
        date.getMinutes(),
        date.getSeconds()
    );
}

function parseOriginTimeInput(value) {
    const raw = (value || "").trim();
    if (!raw) {
        return null;
    }

    // YYYY-MM-DD HH:mm:ss or YYYY-MM-DDTHH:mm:ss (seconds optional)
    const isoLike = raw.match(
        /^(\d{4})-(\d{2})-(\d{2})(?:[T\s]+(\d{1,2}):(\d{2})(?::(\d{2}))?)?(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?$/
    );
    if (isoLike) {
        const year = Number(isoLike[1]);
        const month = Number(isoLike[2]);
        const day = Number(isoLike[3]);
        const hour = Number(isoLike[4] ?? 0);
        const minute = Number(isoLike[5] ?? 0);
        const second = Number(isoLike[6] ?? 0);
        const probe = new Date(year, month - 1, day, hour, minute, second);
        if (
            probe.getFullYear() !== year ||
            probe.getMonth() !== month - 1 ||
            probe.getDate() !== day ||
            probe.getHours() !== hour ||
            probe.getMinutes() !== minute ||
            probe.getSeconds() !== second
        ) {
            return null;
        }
        return toNaiveIsoString(year, month, day, hour, minute, second);
    }

    // dd/mm/yyyy, HH:mm:ss (comma optional; seconds optional)
    const dmy = raw.match(
        /^(\d{1,2})\/(\d{1,2})\/(\d{4})(?:[,\s]+(\d{1,2}):(\d{2})(?::(\d{2}))?)?$/
    );
    if (dmy) {
        const day = Number(dmy[1]);
        const month = Number(dmy[2]);
        const year = Number(dmy[3]);
        const hour = Number(dmy[4] ?? 0);
        const minute = Number(dmy[5] ?? 0);
        const second = Number(dmy[6] ?? 0);
        const probe = new Date(year, month - 1, day, hour, minute, second);
        if (
            probe.getFullYear() !== year ||
            probe.getMonth() !== month - 1 ||
            probe.getDate() !== day ||
            probe.getHours() !== hour ||
            probe.getMinutes() !== minute ||
            probe.getSeconds() !== second
        ) {
            return null;
        }
        return toNaiveIsoString(year, month, day, hour, minute, second);
    }

    return null;
}

function hasEventsPermission() {
    return canManageEvents === true;
}

async function requireEventsAuth(actionLabel = "perform this action") {
    let token = window.localStorage.getItem("access_token");
    if (!token) {
        window.showAlert(
            "alertPlaceholder",
            "danger",
            t("events.error.login", `Please log in to ${actionLabel}.`)
        );
        return false;
    }

    if (window.isTokenExpired?.(token)) {
        window.showAlert(
            "alertPlaceholder",
            "danger",
            t("alerts.session_expired", "Session has expired. Please sign in again.")
        );
        window.clearSessionData?.();
        return false;
    }

    if (!hasEventsPermission()) {
        window.showAlert(
            "alertPlaceholder",
            "danger",
            t("events.error.forbidden", `You do not have permission to ${actionLabel}.`)
        );
        return false;
    }

    return true;
}

let createEventGuardBound = false;

function bindCreateEventAuthGuard() {
    const createEventButton = document.getElementById("btnCreateEvent");
    if (!createEventButton) {
        return;
    }

    if (!canManageEvents) {
        createEventButton.classList.add("d-none");
        return;
    }

    createEventButton.classList.remove("d-none");

    if (createEventGuardBound) {
        return;
    }
    createEventGuardBound = true;

    createEventButton.addEventListener("click", async (event) => {
        event.preventDefault();
        if (!(await requireEventsAuth("add an earthquake"))) {
            return;
        }
        window.openCreateEventModal?.();
    });
}

function syncActionColumnVisibility() {
    if (!eventsActionHeader) {
        return;
    }
    eventsActionHeader.classList.remove("d-none");
}

function eventTypeBadge(event) {
    const automatic = Boolean(event.is_automatic);
    const letter = automatic ? "A" : "C";
    const label = automatic
        ? t("events.type.automatic", "Automatic")
        : t("events.type.calculated", "Calculated (reviewed)");
    return `<span class="published-type published-type-${letter.toLowerCase()}" title="${escapeHtml(
        label
    )}" aria-label="${escapeHtml(label)}">${letter}</span>`;
}

function publishedBadge(event) {
    if (!event.is_published) {
        return `<span class="events-pub events-pub-no">
          <i class="fa-regular fa-circle" aria-hidden="true"></i>${escapeHtml(t("events.published.no", "No"))}
        </span>`;
    }
    const title = event.published_at
        ? t("events.published.at", "Published: {time}").replace(
              "{time}",
              formatOriginTime(event.published_at)
          )
        : "";
    return `<span class="events-pub events-pub-yes"${title ? ` title="${escapeHtml(title)}"` : ""}>
          <i class="fa-solid fa-circle-check" aria-hidden="true"></i>${escapeHtml(t("events.published.yes", "Yes"))}
        </span>`;
}

function depthCell(depth) {
    const value = Number(depth);
    if (depth === null || depth === undefined || depth === "" || !Number.isFinite(value)) {
        return `<span class="text-muted">-</span>`;
    }
    return `<span class="events-depth">${escapeHtml(value.toFixed(1))}</span>`;
}

function timeCell(value) {
    const match = String(value || "").match(/^(\d{4}-\d{2}-\d{2})[T\s](\d{2}:\d{2}:\d{2})/);
    if (!match) {
        return `<span class="events-time">${escapeHtml(formatOriginTime(value))}</span>`;
    }
    return `
          <span class="events-date">${match[1]}</span>
          <span class="events-time">${match[2]} <span class="events-utc">UTC</span></span>`;
}

function magnitudeLevel(value) {
    if (value >= 5) return "major";
    if (value >= 4) return "strong";
    if (value >= 3) return "moderate";
    return "minor";
}

function magnitudeCell(event) {
    const magnitude = getEventMagnitude(event);
    if (!magnitude || Number.isNaN(magnitude.value)) {
        return `<span class="text-muted">-</span>`;
    }
    const code = magnitude.code
        ? `<span class="events-mag-code">${escapeHtml(magnitude.code)}</span>`
        : "";
    return `<span class="events-mag-badge events-mag-${magnitudeLevel(magnitude.value)}"><span class="events-mag-value">${escapeHtml(
        magnitude.value.toFixed(1)
    )}</span>${code}</span>`;
}

const PAGE_SIZE = 20;
const SORT_KEYS = new Set(["time", "magnitude", "depth", "type", "published"]);
let sortState = { key: "time", dir: "desc" };
let currentPage = 1;
let latestEventId = null;
let selectedEventId = null;

function isDefaultSort() {
    return sortState.key === "time" && sortState.dir === "desc";
}

function totalPages() {
    return Math.max(1, Math.ceil((Number(window.eventsListTotal) || 0) / PAGE_SIZE));
}

function syncSortHeaders() {
    document.querySelectorAll(".events-table th[data-sort-key]").forEach((th) => {
        const active = th.dataset.sortKey === sortState.key;
        th.classList.toggle("is-sorted", active);
        th.setAttribute(
            "aria-sort",
            active ? (sortState.dir === "asc" ? "ascending" : "descending") : "none"
        );
        const icon = th.querySelector(".fa-solid");
        if (icon) {
            icon.className = `fa-solid ${
                active ? (sortState.dir === "asc" ? "fa-sort-up" : "fa-sort-down") : "fa-sort"
            }`;
        }
    });
}

function setSort(key) {
    if (!SORT_KEYS.has(key)) {
        return;
    }
    sortState =
        sortState.key === key
            ? { key, dir: sortState.dir === "asc" ? "desc" : "asc" }
            : { key, dir: "desc" };
    applyEventsFilter(window.getActiveEventsFilter?.() || null, { page: 1 });
}

// Page numbers to show: first, last, and the current page with one neighbour each side.
function visiblePages(current, last) {
    const pages = new Set([1, last, current - 1, current, current + 1]);
    const sorted = [...pages].filter((page) => page >= 1 && page <= last).sort((a, b) => a - b);
    const items = [];
    sorted.forEach((page, index) => {
        if (index > 0 && page - sorted[index - 1] > 1) {
            items.push(null);
        }
        items.push(page);
    });
    return items;
}

function renderPagination() {
    const nav = document.getElementById("eventsPagination");
    if (!nav) {
        return;
    }
    const last = totalPages();
    if (last <= 1) {
        nav.innerHTML = "";
        nav.classList.add("d-none");
        return;
    }
    nav.classList.remove("d-none");

    const pageItem = (page, label, { disabled = false, active = false, aria = "" } = {}) => `
        <li class="page-item${disabled ? " disabled" : ""}${active ? " active" : ""}">
          <button type="button" class="page-link" data-page="${page}"${
              disabled ? " disabled" : ""
          }${active ? ' aria-current="page"' : ""}${aria ? ` aria-label="${escapeHtml(aria)}"` : ""}>${label}</button>
        </li>`;

    const items = [
        pageItem(currentPage - 1, '<i class="fa-solid fa-chevron-left" aria-hidden="true"></i>', {
            disabled: currentPage === 1,
            aria: t("events.page.prev", "Previous page"),
        }),
        ...visiblePages(currentPage, last).map((page) =>
            page === null
                ? '<li class="page-item disabled"><span class="page-link">…</span></li>'
                : pageItem(page, String(page), { active: page === currentPage })
        ),
        pageItem(currentPage + 1, '<i class="fa-solid fa-chevron-right" aria-hidden="true"></i>', {
            disabled: currentPage === last,
            aria: t("events.page.next", "Next page"),
        }),
    ];
    nav.innerHTML = `<ul class="pagination pagination-sm justify-content-center flex-wrap mb-0">${items.join("")}</ul>`;
}

function goToPage(page) {
    const target = Math.min(Math.max(1, Number(page) || 1), totalPages());
    if (target === currentPage) {
        return;
    }
    applyEventsFilter(window.getActiveEventsFilter?.() || null, { page: target }).then(() => {
        const card = document.querySelector(".events-list-card");
        if (card && card.getBoundingClientRect().top < 0) {
            card.scrollIntoView({ behavior: "smooth", block: "start" });
        }
    });
}

function findEventRow(eventId) {
    if (!eventsTableBody || eventId === null || eventId === undefined) {
        return null;
    }
    return eventsTableBody.querySelector(`tr[data-event-id="${CSS.escape(String(eventId))}"]`);
}

function selectEventRow(eventId) {
    selectedEventId = eventId === null || eventId === undefined ? null : String(eventId);
    eventsTableBody
        ?.querySelectorAll("tr.is-selected")
        .forEach((row) => row.classList.remove("is-selected"));
    const row = findEventRow(selectedEventId);
    row?.classList.add("is-selected");
    return row;
}

function showEventOnMap(eventId) {
    selectEventRow(eventId);
    if (!window.focusEventOnMap?.(eventId)) {
        return;
    }
    const mapCard = document.getElementById("mapDiv");
    const rect = mapCard?.getBoundingClientRect();
    if (rect && (rect.bottom < 80 || rect.top > window.innerHeight - 80)) {
        mapCard.scrollIntoView({ behavior: "smooth", block: "center" });
    }
}

function renderEvents(events) {
    syncActionColumnVisibility();
    syncSortHeaders();

    if (!eventsTableBody || !eventsStatus) {
        return;
    }

    if (!Array.isArray(events) || events.length === 0) {
        eventsTableBody.innerHTML = "";
        eventsStatus.textContent = t("events.empty", "No events found.");
        renderPagination();
        return;
    }

    const sortedEvents = events;

    eventsById.clear();
    sortedEvents.forEach((event) => eventsById.set(getEventKey(event), event));
    window.eventsById = eventsById;

    const depthLabel = escapeHtml(t("events.table.depth_km", "Depth (km)"));

    eventsTableBody.innerHTML = sortedEvents
        .map((event) => {
            const id = escapeHtml(event.id);
            const selected = selectedEventId !== null && getEventKey(event) === selectedEventId;

            return `
      <tr data-event-id="${id}" tabindex="0"${selected ? ' class="is-selected"' : ""}>
        <td class="events-col-actions">
          <div class="events-actions">
            ${window.buildEventDetailsButton ? window.buildEventDetailsButton(event.id) : ""}
            ${
                canManageEvents
                    ? `
            <button
              type="button"
              class="btn btn-sm btn-outline-secondary events-action-btn"
              data-edit-id="${id}"
              title="${t("events.table.edit", "Edit")}"
              aria-label="${t("events.table.edit", "Edit")}"
            >
              <i class="fa-solid fa-pen"></i>
            </button>
            <button
              type="button"
              class="btn btn-sm btn-outline-danger events-action-btn"
              data-delete-id="${id}"
              title="${t("events.table.delete", "Delete")}"
              aria-label="${t("events.table.delete", "Delete")}"
            >
              <i class="fa-solid fa-trash"></i>
            </button>
            `
                    : ""
            }
          </div>
        </td>
        <td class="events-col-type">${eventTypeBadge(event)}</td>
        <td class="events-col-published">${publishedBadge(event)}</td>
        <td class="events-col-time">${timeCell(event.origin_time)}</td>
        <td class="events-col-mag">${magnitudeCell(event)}</td>
        <td class="events-col-depth" data-label="${depthLabel}">${depthCell(event.depth)}</td>
        <td class="events-col-location">
          <span class="events-location">${escapeHtml(preferredLocation(event))}</span>
        </td>
      </tr>
    `;
        })
        .join("");

    const total = Number.isFinite(Number(window.eventsListTotal))
        ? Number(window.eventsListTotal)
        : sortedEvents.length;
    const from = (currentPage - 1) * PAGE_SIZE + 1;
    eventsStatus.textContent = t("events.showing", "Showing {from}–{to} of {total} earthquakes.")
        .replace("{from}", String(from))
        .replace("{to}", String(from + sortedEvents.length - 1))
        .replace("{total}", String(total));
    renderPagination();
}

function renderEventsAndMap(events) {
    renderEvents(events);
    if (typeof window.updateMapMarkers === "function") {
        window.updateMapMarkers(Array.isArray(events) ? events : [], { latestId: latestEventId });
    }
}

let filterRequestSeq = 0;
let latestFilterKey = null;

function fetchEventsPage(filterState, { limit, offset, sort, order }) {
    if (!filterState || window.isEmptyEventsFilter?.(filterState)) {
        const query = new URLSearchParams({ limit, offset, sort, order });
        return window.makeApiRequest(`/api/seismic_events/?${query}`, { method: "GET" });
    }
    return window.makeApiRequest("/api/seismic_events/filter", {
        method: "POST",
        body: JSON.stringify({
            ...window.buildEventsFilterPayload(filterState),
            limit,
            offset,
            sort,
            order,
        }),
    });
}

// The map marks the newest event matching the filter, whichever page or sort is shown.
async function refreshLatestEventId(filterState, filterKey, items) {
    if (currentPage === 1 && isDefaultSort()) {
        latestEventId = items[0]?.id ?? null;
        latestFilterKey = filterKey;
        return;
    }
    if (latestFilterKey === filterKey) {
        return;
    }
    try {
        const newest = await fetchEventsPage(filterState, {
            limit: 1,
            offset: 0,
            sort: "time",
            order: "desc",
        });
        latestEventId = newest.items?.[0]?.id ?? null;
        latestFilterKey = filterKey;
    } catch {
        latestEventId = null;
    }
}

async function applyEventsFilter(filterState, { page = 1 } = {}) {
    const requestId = ++filterRequestSeq;
    const targetPage = Math.max(1, Number(page) || 1);

    if (eventsStatus) {
        eventsStatus.textContent = t("events.loading", "Loading earthquakes...");
    }

    try {
        const filterKey = JSON.stringify(
            filterState && !window.isEmptyEventsFilter?.(filterState)
                ? window.buildEventsFilterPayload(filterState)
                : {}
        );
        const data = await fetchEventsPage(filterState, {
            limit: PAGE_SIZE,
            offset: (targetPage - 1) * PAGE_SIZE,
            sort: sortState.key,
            order: sortState.dir,
        });

        if (requestId !== filterRequestSeq) {
            return;
        }

        const items = Array.isArray(data.items) ? data.items : [];
        const total = Number.isFinite(Number(data.total)) ? Number(data.total) : items.length;

        // A deletion can empty the last page; fall back to the new last page.
        const lastPage = Math.max(1, Math.ceil(total / PAGE_SIZE));
        if (items.length === 0 && targetPage > lastPage) {
            await applyEventsFilter(filterState, { page: lastPage });
            return;
        }

        currentPage = targetPage;
        allEvents = items;
        window.eventsListTotal = total;
        await refreshLatestEventId(filterState, filterKey, items);
        if (requestId !== filterRequestSeq) {
            return;
        }
        window.updateAreaFilterOptions?.(allEvents);
        renderEventsAndMap(allEvents);
    } catch (error) {
        if (requestId !== filterRequestSeq) {
            return;
        }
        const message = error.message || t("events.error.load", "Failed to load earthquakes.");
        if (eventsTableBody) {
            eventsTableBody.innerHTML = "";
        }
        if (eventsStatus) {
            eventsStatus.textContent = message;
        }
        window.eventsListTotal = 0;
        renderPagination();
        window.showAlert("alertPlaceholder", "danger", message);
    }
}

function reloadEventsPage(page = currentPage) {
    // Edits can change which event is newest, so look it up again.
    latestFilterKey = null;
    return applyEventsFilter(window.getActiveEventsFilter?.() || null, { page });
}

function onEventUpdated() {
    reloadEventsPage();
}

function onEventDeleted() {
    reloadEventsPage();
}

function onEventCreated(event) {
    if (!event?.id) {
        window.loadEvents?.();
        return;
    }
    reloadEventsPage(1);
}

async function loadEvents() {
    if (eventsStatus) {
        eventsStatus.textContent = t("events.loading", "Loading earthquakes...");
    }

    try {
        const token = localStorage.getItem("access_token");
        if (!token || window.isTokenExpired?.(token)) {
            window.showAlert(
                "alertPlaceholder",
                "danger",
                t("alerts.session_expired", "Session has expired. Please sign in again.")
            );
            window.clearSessionData?.();
            return;
        }

        const profile = await window.makeApiRequest("/api/accounts/ourself", {
            method: "GET",
        });
        canManageEvents = Boolean(profile?.can_event_edit);
        canViewEvents = canManageEvents || Boolean(profile?.can_event_view);
        window.canManageEvents = canManageEvents;
        window.canViewEvents = canViewEvents;

        if (!canViewEvents) {
            if (eventsTableBody) {
                eventsTableBody.innerHTML = "";
            }
            if (eventsStatus) {
                eventsStatus.textContent = t(
                    "events.error.forbidden",
                    "You do not have permission to manage earthquakes."
                );
            }
            document.getElementById("btnCreateEvent")?.classList.add("d-none");
            window.showAlert(
                "alertPlaceholder",
                "danger",
                t(
                    "events.error.forbidden",
                    "You do not have permission to manage earthquakes."
                )
            );
            const i18n = window.I18n;
            window.location.href = i18n ? i18n.localizePath("/") : "/";
            return;
        }

        bindCreateEventAuthGuard();

        const currentFilter = window.getActiveEventsFilter?.() || null;
        await applyEventsFilter(currentFilter);
    } catch (error) {
        if (eventsTableBody) {
            eventsTableBody.innerHTML = "";
        }
        if (eventsStatus) {
            eventsStatus.textContent =
                error.message || t("events.error.load", "Failed to load earthquakes.");
        }
        window.showAlert(
            "alertPlaceholder",
            "danger",
            error.message || t("events.error.load", "Failed to load earthquakes.")
        );
    }
}

window.escapeHtml = escapeHtml;
window.formatOriginTime = formatOriginTime;
window.parseOriginTimeInput = parseOriginTimeInput;
window.getEventMl = getEventMl;
window.getEventMagnitude = getEventMagnitude;
window.requireEventsAuth = requireEventsAuth;
window.hasPermission = (code) => {
    if (code === "can_event_edit") {
        return canManageEvents;
    }
    if (code === "can_event_view") {
        return canViewEvents;
    }
    return false;
};
window.renderEvents = renderEvents;
window.renderEventsAndMap = renderEventsAndMap;
window.applyEventsFilter = applyEventsFilter;
window.loadEvents = loadEvents;
window.onEventUpdated = onEventUpdated;
window.onEventDeleted = onEventDeleted;
window.onEventCreated = onEventCreated;
window.eventsById = eventsById;
window.onMapEventSelected = selectEventRow;

document.addEventListener("DOMContentLoaded", () => {
    eventsTableBody?.addEventListener("click", (event) => {
        const editButton = event.target.closest("[data-edit-id]");
        if (editButton) {
            window.openEditEventModal?.(editButton.dataset.editId);
            return;
        }

        const deleteButton = event.target.closest("[data-delete-id]");
        if (deleteButton) {
            const eventId = deleteButton.dataset.deleteId;
            const rowEvent = eventsById.get(Number(eventId));
            window.deleteEvent?.(eventId, {
                isPublished: Boolean(rowEvent?.is_published),
            });
            return;
        }

        if (event.target.closest("a, button")) {
            return;
        }
        const row = event.target.closest("tr[data-event-id]");
        if (row) {
            showEventOnMap(row.dataset.eventId);
        }
    });

    eventsTableBody?.addEventListener("keydown", (event) => {
        if (event.key !== "Enter" || event.target.tagName !== "TR") {
            return;
        }
        event.preventDefault();
        showEventOnMap(event.target.dataset.eventId);
    });

    document.querySelector(".events-table thead")?.addEventListener("click", (event) => {
        const sortButton = event.target.closest("[data-sort]");
        if (sortButton) {
            setSort(sortButton.dataset.sort);
        }
    });

    document.getElementById("eventsPagination")?.addEventListener("click", (event) => {
        const pageButton = event.target.closest("[data-page]");
        if (pageButton && !pageButton.disabled) {
            goToPage(pageButton.dataset.page);
        }
    });

    loadEvents().then(() => {
        const editId = new URLSearchParams(window.location.search).get("edit");
        if (editId && canManageEvents) {
            window.openEditEventModal?.(editId);
            const url = new URL(window.location.href);
            url.searchParams.delete("edit");
            window.history.replaceState({}, "", url.pathname + url.search);
        }
    });
});
