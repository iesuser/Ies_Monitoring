const EVENT_DETAILS_ALERT_ID = "eventDetailsAlertPlaceholder";

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

function formatOriginTime(value) {
    if (!value) {
        return "—";
    }
    const raw = String(value).trim();
    const isoMatch = raw.match(
        /^(\d{4})-(\d{2})-(\d{2})[T\s](\d{2}):(\d{2})(?::(\d{2}))?/
    );
    if (isoMatch) {
        const pad = (n) => String(n).padStart(2, "0");
        return (
            `${isoMatch[1]}-${isoMatch[2]}-${isoMatch[3]}T` +
            `${pad(Number(isoMatch[4]))}:${pad(Number(isoMatch[5]))}:${pad(
                Number(isoMatch[6] ?? 0)
            )}`
        );
    }
    return raw;
}

function preferredLocation(event) {
    const lang = window.I18n?.getLanguage?.() || "en";
    if (lang === "ka") {
        return event.location_ge || event.location_en || event.area || event.seiscomp_oid || `#${event.id}`;
    }
    return event.location_en || event.location_ge || event.area || event.seiscomp_oid || `#${event.id}`;
}

function formatArea(area) {
    if (!area) {
        return t("events.area.unset", "Not specified");
    }
    return t(`events.area.${area}`, area);
}

function getPreferredMagnitude(event) {
    const list = (Array.isArray(event?.magnitudes) ? event.magnitudes : []).filter(
        (item) => item.value !== null && item.value !== undefined
    );
    if (!list.length) {
        return null;
    }
    const preferred =
        list.find((item) => (item.magnitude?.code || "").toUpperCase() === "ML") || list[0];
    return {
        value: Number(preferred.value),
        code: preferred.magnitude?.code || "",
    };
}

function displayOrDash(value) {
    return value === null || value === undefined || value === "" ? "—" : value;
}

function formatActor(actor) {
    if (!actor?.name) {
        return "—";
    }
    if (actor.kind === "service") {
        return `${actor.name} (${t("events.details.actor_service", "service")})`;
    }
    return actor.name;
}

function metadataItem(label, value, monospace = false) {
    return `
        <div class="metadata-item">
            <div class="event-summary-label">${escapeHtml(label)}</div>
            <div class="event-summary-value ${monospace ? "font-monospace" : ""}">${escapeHtml(
                displayOrDash(value)
            )}</div>
        </div>
    `;
}

function renderSummary(event) {
    const container = document.getElementById("eventDetailsSummary");
    const title = document.getElementById("eventDetailsTitle");
    if (title) {
        title.textContent = `${t("events.details.event_prefix", "Event")}: ${preferredLocation(event)}`;
    }
    if (!container) {
        return;
    }

    const magnitude = getPreferredMagnitude(event);
    const magnitudeHtml = magnitude
        ? `${escapeHtml(magnitude.value.toFixed(1))}<span class="event-summary-unit">${escapeHtml(
              magnitude.code || "ML"
          )}</span>`
        : "—";
    const depthHtml =
        event.depth === null || event.depth === undefined
            ? "—"
            : `${escapeHtml(Number(event.depth).toFixed(1))} <span class="event-summary-unit">km</span>`;
    const latLon =
        event.latitude === null ||
        event.latitude === undefined ||
        event.longitude === null ||
        event.longitude === undefined
            ? "—"
            : `${Number(event.latitude).toFixed(4)}, ${Number(event.longitude).toFixed(4)}`;

    container.innerHTML = `
        <div class="event-summary-grid">
            <div class="event-summary-item">
                <div class="event-summary-label" data-i18n="events.edit.origin_time">Origin Time (ISO 8601)</div>
                <div class="event-summary-value">${escapeHtml(formatOriginTime(event.origin_time))}</div>
            </div>
            <div class="event-summary-item">
                <div class="event-summary-label" data-i18n="events.table.ml">Magnitude</div>
                <div class="event-summary-value">${magnitudeHtml}</div>
            </div>
            <div class="event-summary-item">
                <div class="event-summary-label" data-i18n="events.edit.depth">Depth (km)</div>
                <div class="event-summary-value">${depthHtml}</div>
            </div>
            <div class="event-summary-item">
                <div class="event-summary-label" data-i18n="events.details.lat_lon">Lat / Lon</div>
                <div class="event-summary-value font-monospace">${escapeHtml(latLon)}</div>
            </div>
            <div class="event-summary-item">
                <div class="event-summary-label" data-i18n="events.table.id">Event ID</div>
                <div class="event-summary-value">${escapeHtml(event.id)}</div>
            </div>
        </div>
        <div class="event-summary-meta">
            <span class="text-muted">
                SeisComP OID:
                <code>${escapeHtml(event.seiscomp_oid || "—")}</code>
            </span>
            <span class="text-muted">
                IES data ID:
                <code>${escapeHtml(event.iesdata_id || "—")}</code>
            </span>
            <span class="badge ${event.is_automatic ? "text-bg-info text-dark" : "text-bg-secondary"}">
                ${escapeHtml(
                    event.is_automatic
                        ? t("events.details.automatic", "Automatic")
                        : t("events.details.manual", "Manual")
                )}
            </span>
        </div>
    `;
}

function renderOverview(event) {
    const container = document.getElementById("eventDetailsOverview");
    if (!container) {
        return;
    }

    container.innerHTML = [
        metadataItem(t("events.table.id", "Event ID"), event.id),
        metadataItem(t("events.edit.iesdata_id", "IES data ID"), event.iesdata_id, true),
        metadataItem(t("events.edit.seiscomp_oid", "SeisComP OID"), event.seiscomp_oid, true),
        metadataItem(
            t("events.edit.origin_time", "Origin Time (ISO 8601)"),
            formatOriginTime(event.origin_time),
            true
        ),
        metadataItem(
            t("events.edit.depth", "Depth (km)"),
            event.depth === null || event.depth === undefined
                ? "—"
                : Number(event.depth).toFixed(1)
        ),
        metadataItem(
            t("events.edit.latitude", "Latitude"),
            event.latitude === null || event.latitude === undefined
                ? "—"
                : Number(event.latitude).toFixed(4),
            true
        ),
        metadataItem(
            t("events.edit.longitude", "Longitude"),
            event.longitude === null || event.longitude === undefined
                ? "—"
                : Number(event.longitude).toFixed(4),
            true
        ),
        metadataItem(t("events.edit.location_ge", "Location GE"), event.location_ge),
        metadataItem(t("events.edit.location_en", "Location EN"), event.location_en),
        metadataItem(t("events.edit.area", "Area"), formatArea(event.area)),
        metadataItem(
            t("events.details.is_automatic", "Automatic"),
            event.is_automatic ? t("events.details.yes", "Yes") : t("events.details.no", "No")
        ),
        metadataItem(
            t("events.details.created_at", "Created at"),
            formatOriginTime(event.created_at),
            true
        ),
        metadataItem(t("events.details.created_by", "Created by"), formatActor(event.created_by)),
        metadataItem(
            t("events.details.updated_at", "Last updated"),
            event.updated_at ? formatOriginTime(event.updated_at) : "—",
            true
        ),
        metadataItem(t("events.details.updated_by", "Updated by"), formatActor(event.updated_by)),
    ].join("");
}

function renderMagnitudes(magnitudes) {
    const container = document.getElementById("eventDetailsMagnitudes");
    if (!container) {
        return;
    }

    const list = Array.isArray(magnitudes) ? magnitudes : [];
    if (!list.length) {
        container.innerHTML = `<p class="text-muted mb-0">${escapeHtml(
            t("events.edit.magnitudes_empty", "No magnitudes recorded.")
        )}</p>`;
        return;
    }

    container.innerHTML = `
        <div class="table-responsive">
            <table class="table table-sm align-middle mb-0">
                <thead class="table-light">
                    <tr>
                        <th data-i18n="events.create.magnitude_type">Magnitude type</th>
                        <th data-i18n="events.create.magnitude_value">Magnitude value</th>
                    </tr>
                </thead>
                <tbody>
                    ${list
                        .map((item) => {
                            const code = item.magnitude?.code || "—";
                            const value =
                                item.value === null || item.value === undefined
                                    ? "—"
                                    : Number(item.value).toFixed(1);
                            return `
                                <tr>
                                    <td class="font-monospace">${escapeHtml(code)}</td>
                                    <td>${escapeHtml(value)}</td>
                                </tr>
                            `;
                        })
                        .join("")}
                </tbody>
            </table>
        </div>
    `;
}

function renderBeachball(beachball) {
    const container = document.getElementById("eventDetailsBeachball");
    if (!container) {
        return;
    }

    if (!beachball) {
        container.innerHTML = `<p class="text-muted mb-0">${escapeHtml(
            t("events.edit.beachball_empty", "No beachball data.")
        )}</p>`;
        return;
    }

    const cacheBust = Date.now();
    const imageHtml = beachball.beachball_path
        ? `
            <div class="text-center mb-3">
                <img
                    src="${escapeHtml(beachball.beachball_path)}?t=${cacheBust}"
                    alt="Beachball"
                    class="img-fluid event-details-beachball-img"
                >
            </div>
        `
        : "";

    container.innerHTML = `
        <div class="beachball-panel">
            ${imageHtml}
            <div class="metadata-grid">
                ${metadataItem(t("events.edit.beachball_strike", "Strike"), beachball.strike)}
                ${metadataItem(t("events.edit.beachball_dip", "Dip"), beachball.dip)}
                ${metadataItem(t("events.edit.beachball_rake", "Rake"), beachball.rake)}
            </div>
        </div>
    `;
}

function goToEventsList() {
    const path = window.I18n?.localizePath?.("/seismic_events") || "/seismic_events";
    window.location.href = path;
}

function applyEventToPage(event, permissions) {
    document.title = `IES Monitoring | Event ${event.id}`;
    renderSummary(event);
    renderPublishPanel(event, permissions);
    renderOverview(event);
    renderMagnitudes(event.magnitudes);
    renderBeachball(event.beachball);
    window.renderEventShakeMap?.(event);
    renderActions(event, permissions);
    window.I18n?.applyTranslations?.();
}

function renderPublishPanel(event, permissions = {}) {
    const container = document.getElementById("eventDetailsPublish");
    if (!container) {
        return;
    }

    const isPublished = Boolean(event.is_published);
    const canPublish = Boolean(permissions.canPublish);
    const statusText = isPublished
        ? t("events.publish.published", "Published")
        : t("events.publish.not_published", "Not published");
    const publishedAtText = isPublished
        ? `${t("events.publish.published_at", "Published at")}: ${formatOriginTime(
              event.published_at
          )}`
        : t(
              "events.publish.hint_unpublished",
              "This earthquake is not visible on the public website."
          );

    let actionsHtml = "";
    if (canPublish) {
        if (isPublished) {
            actionsHtml = `
                <div class="event-publish-actions">
                    <button
                        type="button"
                        class="btn btn-outline-success"
                        id="eventDetailsPublishBtn"
                        data-i18n="events.publish.update"
                    >
                        Update publish
                    </button>
                    <button
                        type="button"
                        class="btn btn-warning"
                        id="eventDetailsUnpublishBtn"
                        data-i18n="events.publish.unpublish"
                    >
                        Unpublish
                    </button>
                </div>
            `;
        } else {
            actionsHtml = `
                <div class="event-publish-actions">
                    <button
                        type="button"
                        class="btn btn-success"
                        id="eventDetailsPublishBtn"
                        data-i18n="events.publish.action"
                    >
                        Publish
                    </button>
                </div>
            `;
        }
    }

    container.classList.remove("d-none", "is-published", "is-unpublished");
    container.classList.add(isPublished ? "is-published" : "is-unpublished");
    container.innerHTML = `
        <div class="event-publish-row">
            <div class="event-publish-status">
                <div class="event-publish-status-icon" aria-hidden="true">
                    <i class="fa-solid ${isPublished ? "fa-globe" : "fa-eye-slash"}"></i>
                </div>
                <div>
                    <div
                        class="event-publish-status-label"
                        data-i18n="events.publish.status_label"
                    >
                        Publication status
                    </div>
                    <div class="event-publish-status-value">${escapeHtml(statusText)}</div>
                    <div class="event-publish-status-meta">${escapeHtml(publishedAtText)}</div>
                </div>
            </div>
            ${actionsHtml}
        </div>
    `;

    document.getElementById("eventDetailsPublishBtn")?.addEventListener("click", () => {
        publishOrUnpublishEvent(event, true, permissions);
    });
    document.getElementById("eventDetailsUnpublishBtn")?.addEventListener("click", () => {
        publishOrUnpublishEvent(event, false, permissions);
    });
}

function setPublishPanelBusy(isPublish, wasPublished) {
    const container = document.getElementById("eventDetailsPublish");
    if (!container) {
        return;
    }

    const statusText = isPublish
        ? wasPublished
            ? t("events.publish.updating", "Updating publication...")
            : t("events.publish.publishing", "Publishing...")
        : t("events.publish.unpublishing", "Unpublishing...");

    container.classList.add("is-busy");
    container.setAttribute("aria-busy", "true");

    const icon = container.querySelector(".event-publish-status-icon i");
    if (icon) {
        icon.className = "fa-solid fa-arrows-rotate fa-spin";
    }
    const value = container.querySelector(".event-publish-status-value");
    if (value) {
        value.textContent = statusText;
    }
    const meta = container.querySelector(".event-publish-status-meta");
    if (meta) {
        meta.textContent = t(
            "events.publish.wait",
            "Sending the request to the public website, please wait..."
        );
    }
    container.querySelectorAll(".event-publish-actions .btn").forEach((button) => {
        button.disabled = true;
    });
}

async function publishOrUnpublishEvent(event, publish, permissions) {
    const isPublish = Boolean(publish);
    const wasPublished = Boolean(event.is_published);
    const confirmMessage = isPublish
        ? wasPublished
            ? t(
                  "events.publish.update_confirm",
                  "Update this earthquake on the public website?"
              )
            : t(
                  "events.publish.confirm",
                  "Publish this earthquake to the public website?"
              )
        : t(
              "events.publish.unpublish_confirm",
              "Unpublish this earthquake from the public website?"
          );

    const confirmed = await window.confirmDelete?.({
        title: isPublish
            ? wasPublished
                ? t("events.publish.update", "Update publish")
                : t("events.publish.action", "Publish")
            : t("events.publish.unpublish", "Unpublish"),
        message: confirmMessage,
        confirmText: isPublish
            ? wasPublished
                ? t("events.publish.update", "Update publish")
                : t("events.publish.action", "Publish")
            : t("events.publish.unpublish", "Unpublish"),
    });
    if (!confirmed) {
        return;
    }

    const path = isPublish
        ? `/api/publish_events/publish/${event.id}`
        : `/api/publish_events/unpublish/${event.id}`;

    setPublishPanelBusy(isPublish, wasPublished);

    try {
        const data = await window.makeApiRequest(path, { method: "POST" });
        const updated = data?.event
            ? data.event
            : {
                  ...event,
                  is_published: Boolean(data?.published),
                  published_at: data?.published ? event.published_at : null,
              };
        applyEventToPage(updated, permissions);
        window.showAlert(
            EVENT_DETAILS_ALERT_ID,
            "success",
            data?.message ||
                (isPublish
                    ? wasPublished
                        ? t(
                              "events.publish.update_success",
                              "Published earthquake updated successfully."
                          )
                        : t("events.publish.success", "Earthquake published successfully.")
                    : t(
                          "events.publish.unpublish_success",
                          "Earthquake unpublished successfully."
                      ))
        );
    } catch (error) {
        renderPublishPanel(event, permissions);
        window.I18n?.applyTranslations?.();
        window.showAlert(
            EVENT_DETAILS_ALERT_ID,
            "danger",
            error.message ||
                (isPublish
                    ? t("events.publish.error", "Failed to publish earthquake.")
                    : t(
                          "events.publish.unpublish_error",
                          "Failed to unpublish earthquake."
                      ))
        );
    }
}

function renderActions(event, permissions = {}) {
    const container = document.getElementById("eventDetailsActions");
    if (!container) {
        return;
    }

    const canManage = Boolean(permissions.canManage);

    if (!canManage) {
        container.innerHTML = "";
        return;
    }

    container.innerHTML = `
        <button
            type="button"
            class="btn btn-outline-secondary"
            id="eventDetailsEditBtn"
            data-i18n="events.table.edit"
        >
            Edit
        </button>
        <button
            type="button"
            class="btn btn-outline-danger"
            id="eventDetailsDeleteBtn"
            data-i18n="events.table.delete"
        >
            Delete
        </button>
    `;
    window.I18n?.applyTranslations?.();

    document.getElementById("eventDetailsEditBtn")?.addEventListener("click", () => {
        window.openEditEventModal?.(event.id);
    });

    document.getElementById("eventDetailsDeleteBtn")?.addEventListener("click", async () => {
        if (event.is_published) {
            window.showAlert(
                EVENT_DETAILS_ALERT_ID,
                "warning",
                t(
                    "events.delete.published_blocked",
                    "This earthquake is published. Unpublish it first, then delete it."
                )
            );
            return;
        }

        const confirmed = await window.confirmDelete?.({
            message: t(
                "events.delete.confirm",
                "Are you sure you want to delete this earthquake?"
            ),
        });
        if (!confirmed) {
            return;
        }

        try {
            await window.makeApiRequest(`/api/seismic_events/event_id=${event.id}`, {
                method: "DELETE",
            });
            goToEventsList();
        } catch (error) {
            window.showAlert(
                EVENT_DETAILS_ALERT_ID,
                error.code === "conflict" ? "warning" : "danger",
                error.message || t("events.error.delete", "Failed to delete earthquake.")
            );
        }
    });
}

function showContent() {
    document.getElementById("eventDetailsLoading")?.classList.add("d-none");
    document.getElementById("eventDetailsContent")?.classList.remove("d-none");
}

function showLoadingError(message) {
    document.getElementById("eventDetailsLoading")?.classList.add("d-none");
    window.showAlert(EVENT_DETAILS_ALERT_ID, "danger", message);
}

async function loadEventDetails() {
    const page = document.getElementById("eventDetailsPage");
    const eventId = page?.dataset?.eventId;
    if (!eventId) {
        showLoadingError(t("events.error.load_detail", "Failed to load event details."));
        return;
    }

    try {
        const token = localStorage.getItem("access_token");
        if (!token || window.isTokenExpired?.(token)) {
            window.showAlert(
                EVENT_DETAILS_ALERT_ID,
                "danger",
                t("alerts.session_expired", "Session has expired. Please sign in again.")
            );
            window.clearSessionData?.();
            document.getElementById("eventDetailsLoading")?.classList.add("d-none");
            return;
        }

        const profile = await window.makeApiRequest("/api/accounts/ourself", {
            method: "GET",
        });
        const permissions = {
            canManage: Boolean(profile?.can_event_edit),
            canPublish: Boolean(profile?.can_event_publish),
        };
        const canView =
            permissions.canManage ||
            permissions.canPublish ||
            Boolean(profile?.can_event_view);

        if (!canView) {
            showLoadingError(
                t(
                    "events.error.forbidden",
                    "You do not have permission to manage earthquakes."
                )
            );
            const i18n = window.I18n;
            window.location.href = i18n ? i18n.localizePath("/") : "/";
            return;
        }

        const event = await window.makeApiRequest(`/api/seismic_events/event_id=${eventId}`, {
            method: "GET",
        });

        window.onEventUpdated = (updated) => {
            if (!updated?.id) {
                loadEventDetails();
                return;
            }
            applyEventToPage(updated, permissions);
        };
        window.onEventDeleted = () => {
            goToEventsList();
        };

        applyEventToPage(event, permissions);
        showContent();
    } catch (error) {
        showLoadingError(
            error.message || t("events.error.load_detail", "Failed to load event details.")
        );
    }
}

document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("tab-shakemap")?.addEventListener("shown.bs.tab", () => {
        window.refreshShakeMap?.();
    });
    loadEventDetails();
});
