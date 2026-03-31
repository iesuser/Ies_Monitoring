const eventsTableBody = document.getElementById("eventsTableBody");
const eventsStatus = document.getElementById("eventsStatus");
const refreshEventsBtn = document.getElementById("refreshEventsBtn");
const lastUpdated = document.getElementById("lastUpdated");
const totalEvents = document.getElementById("totalEvents");

// უსაფრთხო escape, რომ HTML ინექცია არ მოხდეს ცხრილში.
function escapeHtml(value) {
  const div = document.createElement("div");
  div.textContent = value ?? "";
  return div.innerHTML;
}

// აბრუნებს ყველაზე ახალ created_at დროს ივენთების სიიდან.
function getLatestCreatedAt(events) {
  const latest = events.reduce((maxDate, event) => {
    const createdAt = new Date(event.created_at || 0);
    if (Number.isNaN(createdAt.getTime())) {
      return maxDate;
    }
    return createdAt > maxDate ? createdAt : maxDate;
  }, new Date(0));

  if (latest.getTime() === 0) {
    return "—";
  }

  return latest.toLocaleString();
}

// ივენთების ცხრილის რენდერი და ზედა სტატუსების განახლება.
function renderEvents(events) {
  if (!Array.isArray(events) || events.length === 0) {
    eventsTableBody.innerHTML = "";
    eventsStatus.textContent = "ივენთები ვერ მოიძებნა.";
    totalEvents.textContent = "0";
    lastUpdated.textContent = "—";
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
        <td>
          ${
            event.shakemap_calculated
              ? '<span class="badge text-bg-success" title="დათვლილია">✓</span>'
              : '<span class="badge text-bg-danger" title="არ არის დათვლილი">✗</span>'
          }
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

  eventsStatus.textContent = `ჩაიტვირთა ${sortedEvents.length} ივენთი.`;
  totalEvents.textContent = String(sortedEvents.length);
  lastUpdated.textContent = getLatestCreatedAt(sortedEvents);
}

// /api/events-დან მონაცემების წამოღება და UI-ის განახლება.
async function loadEvents() {
  eventsStatus.textContent = "ივენთები იტვირთება...";
  refreshEventsBtn.disabled = true;

  try {
    const response = await fetch("/api/events", {
      method: "GET",
      headers: { accept: "application/json" },
    });
    const payload = await response.json();

    if (!response.ok) {
      eventsTableBody.innerHTML = "";
      eventsStatus.textContent = payload.error || "ივენთების ჩატვირთვა ვერ მოხერხდა.";
      totalEvents.textContent = "—";
      lastUpdated.textContent = "—";
      return;
    }

    renderEvents(payload);
  } catch (error) {
    eventsTableBody.innerHTML = "";
    eventsStatus.textContent = "მოთხოვნა ჩავარდა ივენთების ჩატვირთვისას.";
    totalEvents.textContent = "—";
    lastUpdated.textContent = "—";
  } finally {
    refreshEventsBtn.disabled = false;
  }
}

// Refresh ღილაკი და საწყისი ჩატვირთვა.
refreshEventsBtn.addEventListener("click", loadEvents);
loadEvents();
