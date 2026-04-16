const eventFilterFormElement = document.getElementById("eventFilterForm");
const resetEventFiltersBtn = document.getElementById("resetEventFiltersBtn");
const filterStatus = document.getElementById("eventsStatus");

function buildFilterQuery() {
    const params = new URLSearchParams();

    const eventId = document.getElementById("filterEventId")?.value.trim();
    const seiscompOid = document.getElementById("filterSeiscompOid")?.value.trim();
    const region = document.getElementById("filterRegion")?.value.trim();
    const area = document.getElementById("filterArea")?.value.trim();
    const mlMin = document.getElementById("filterMlMin")?.value.trim();
    const mlMax = document.getElementById("filterMlMax")?.value.trim();
    const depthMin = document.getElementById("filterDepthMin")?.value.trim();
    const depthMax = document.getElementById("filterDepthMax")?.value.trim();
    const startTime = document.getElementById("filterStartTime")?.value.trim();
    const endTime = document.getElementById("filterEndTime")?.value.trim();

    if (eventId) params.set("event_id", eventId);
    if (seiscompOid) params.set("seiscomp_oid", seiscompOid);
    if (region) params.set("region", region);
    if (area) params.set("area", area);
    if (mlMin) params.set("ml_min", mlMin);
    if (mlMax) params.set("ml_max", mlMax);
    if (depthMin) params.set("depth_min", depthMin);
    if (depthMax) params.set("depth_max", depthMax);
    if (startTime) params.set("start_time", startTime);
    if (endTime) params.set("end_time", endTime);

    return params.toString();
}

function filterEventForm(event) {
    if (event && typeof event.preventDefault === "function") {
        event.preventDefault();
    }

    if (filterStatus) {
        filterStatus.textContent = "ფილტრაცია მიმდინარეობს...";
    }

    const query = buildFilterQuery();
    const url = query ? `/api/filter_event?${query}` : "/api/filter_event";

    makeApiRequest(url, {
        method: "POST",
        headers: {
            accept: "application/json",
        },
    })
    .then((data) => {
        if (!Array.isArray(data)) {
            if (window.renderEventsAndMap) window.renderEventsAndMap([]);
            if (filterStatus) {
                filterStatus.textContent = data?.error || "ფილტრაცია ვერ შესრულდა.";
            }
            return;
        }

        if (window.renderEventsAndMap) {
            window.renderEventsAndMap(data);
        }

        if (filterStatus) {
            filterStatus.textContent = `გაფილტრულია ${data.length} მიწისძვრა.`;
        }
    })
    .catch((error) => {
        console.error("Error fetching filtered events:", error);
        if (window.renderEventsAndMap) window.renderEventsAndMap([]);
        if (filterStatus) {
            filterStatus.textContent = "ფილტრაციის მოთხოვნა ჩავარდა.";
        }
    });

    return false;
}

window.filterEventForm = filterEventForm;

if (eventFilterFormElement) {
    eventFilterFormElement.addEventListener("submit", filterEventForm);
}

if (resetEventFiltersBtn) {
    resetEventFiltersBtn.addEventListener("click", async () => {
        eventFilterFormElement.reset();
        if (window.loadEvents) {
            await window.loadEvents();
        }
    });
}