function t(key, fallback) {
    const i18n = window.I18n;
    return i18n ? i18n.t(key, fallback) : fallback;
}

async function deleteEvent(eventId, options = {}) {
    if (!eventId) {
        return;
    }

    if (!(await window.requireEventsAuth?.("delete an earthquake"))) {
        return;
    }

    if (options.isPublished) {
        window.showAlert(
            options.alertId || "alertPlaceholder",
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

    try {
        const data = await window.makeApiRequest(`/api/seismic_events/event_id=${eventId}`, {
            method: "DELETE",
        });
        window.onEventDeleted?.(eventId);
        window.showAlert(
            options.alertId || "alertPlaceholder",
            "success",
            data.message || t("events.delete.success", "Earthquake deleted successfully.")
        );
    } catch (error) {
        window.showAlert(
            options.alertId || "alertPlaceholder",
            error.code === "conflict" ? "warning" : "danger",
            error.message || t("events.error.delete", "Failed to delete earthquake.")
        );
    }
}

window.deleteEvent = deleteEvent;
