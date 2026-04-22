const eventsTableBody = document.getElementById("eventsTableBody");
const eventsStatus = document.getElementById("eventsStatus");
const lastUpdated = document.getElementById("lastUpdated");
const totalEvents = document.getElementById("totalEvents");
const galleryModalElement = document.getElementById("galleryModal");
const galleryModalBody = document.getElementById("galleryModalBody");
const galleryModalLabel = document.getElementById("galleryModalLabel");
const galleryModal = galleryModalElement ? new bootstrap.Modal(galleryModalElement) : null;

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

// გალერეის ღილაკებზე handler-ების მიბმა.
function bindGalleryButtons() {
  const buttons = document.querySelectorAll(".open-gallery-btn");
  buttons.forEach((button) => {
    button.addEventListener("click", () => {
      openGallery(button.dataset.seiscompOid);
    });
  });
}

// რეგენერაციის ღილაკებზე handler-ების მიბმა.
function bindRegenerateButtons() {
  const buttons = document.querySelectorAll(".regenerate-shakemap-btn");
  buttons.forEach((button) => {
    button.addEventListener("click", async () => {
      await regenerateShakeMap(button);
    });
  });
}

// API key-ს ვიმახსოვრებთ localStorage-ში.
function getApiKey() {
  let apiKey = window.localStorage.getItem("ies_api_key");
  if (!apiKey) {
    apiKey = window.prompt("შეიყვანე X-API-Key ShakeMap გენერაციისთვის:");
    if (apiKey) {
      window.localStorage.setItem("ies_api_key", apiKey);
    }
  }
  return apiKey;
}

// არჩევითი რეგენერაცია ცხრილიდან კონკრეტული OID-ით.
async function regenerateShakeMap(button) {
  const seiscompOid = button.dataset.seiscompOid;
  if (!seiscompOid) {
    eventsStatus.textContent = "SeisComP OID არ არის მითითებული.";
    return;
  }

  const accessToken = window.localStorage.getItem("access_token");
  let apiKey = null;
  // თუ JWT ავტორიზაცია არსებობს, API key აღარ არის სავალდებულო.
  if (!accessToken) {
    apiKey = getApiKey();
    if (!apiKey) {
      eventsStatus.textContent = "რეგენერაციისთვის საჭიროა ავტორიზაცია ან API key.";
      return;
    }
  }

  button.disabled = true;
  button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
  eventsStatus.textContent = `ShakeMap გენერაცია დაიწყო (${seiscompOid})...`;

  try {
    const requestHeaders = {
      "Content-Type": "application/json",
      accept: "application/json",
    };
    if (apiKey) {
      requestHeaders["X-API-Key"] = apiKey;
    }

    let payload;
    if (accessToken && typeof window.makeApiRequest === "function") {
      payload = await window.makeApiRequest("/api/shakemap", {
        method: "POST",
        headers: requestHeaders,
        body: JSON.stringify({ seiscomp_oid: seiscompOid }),
      });
      if (!payload || payload.error) {
        eventsStatus.textContent = payload?.error || "ShakeMap გენერაცია ვერ მოხერხდა.";
        return;
      }
    } else {
      const response = await fetch("/api/shakemap", {
        method: "POST",
        headers: requestHeaders,
        body: JSON.stringify({ seiscomp_oid: seiscompOid }),
      });
      payload = await response.json();

      if (!response.ok) {
        eventsStatus.textContent = payload.error || "ShakeMap გენერაცია ვერ მოხერხდა.";
        return;
      }
    }

    eventsStatus.textContent = `ShakeMap წარმატებით დაგენერირდა (${seiscompOid}).`;
    await loadEvents();
  } catch (error) {
    eventsStatus.textContent = "მოთხოვნა ჩავარდა ShakeMap გენერაციისას.";
  } finally {
    button.disabled = false;
    button.innerHTML = '<i class="fas fa-rotate-right"></i>';
  }
}

// seiscomp_oid-ის მიხედვით ShakeMap სურათების გამოტანა modal-ში.
async function openGallery(seiscompOid) {
  if (!galleryModal) {
    return;
  }

  galleryModalLabel.textContent = `ShakeMap გალერეა (${seiscompOid})`;
  galleryModalBody.innerHTML = '<p class="text-muted mb-0">სურათები იტვირთება...</p>';
  galleryModal.show();

  try {
    const response = await fetch(`/api/shakemap/${encodeURIComponent(seiscompOid)}`, {
      method: "GET",
      headers: { accept: "application/json" },
    });
    const payload = await response.json();

    if (!response.ok) {
      galleryModalBody.innerHTML = `<div class="alert alert-danger mb-0">${
        escapeHtml(payload.error || "გალერეის ჩატვირთვა ვერ მოხერხდა.")
      }</div>`;
      return;
    }

    const cards = payload.images
      .map((image) => {
        if (!image.exists) {
          return `
            <div class="col-md-4">
              <div class="card h-100">
                <div class="card-body d-flex align-items-center justify-content-center text-muted">
                  ${escapeHtml(image.filename)} არ არსებობს
                </div>
              </div>
            </div>
          `;
        }

        return `
          <div class="col-md-4">
            <div class="d-flex align-items-center justify-content-center"> 
              <p class="card-text mb-0 text-center fw-semibold">${escapeHtml(image.filename)}</p>
            </div>
            <div class="card h-90 shadow-sm">
              <a
                href="${escapeHtml(image.url)}"
                target="_blank"
                rel="noopener noreferrer"
                title="სრული ზომით გახსნა ახალ ტაბში"
              >
                <img
                  src="${escapeHtml(image.url)}"
                  class="card-img-top"
                  alt="${escapeHtml(image.filename)}"
                  loading="lazy"
                  style="cursor: zoom-in;"
                >
              </a>

            </div>
          </div>
        `;
      })
      .join("");

    galleryModalBody.innerHTML = `
      <div class="mb-3">
        <span class="badge text-bg-secondary">products_path</span>
        <code class="ms-2">${escapeHtml(payload.products_path)}</code>
      </div>
      <div class="row g-3">
        ${cards}
      </div>
    `;
  } catch (error) {
    galleryModalBody.innerHTML = '<div class="alert alert-danger mb-0">მოთხოვნა ჩავარდა გალერეის ჩატვირთვისას.</div>';
  }
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
          <button
            type="button"
            class="btn btn-sm btn-outline-warning ms-2 regenerate-shakemap-btn"
            data-seiscomp-oid="${escapeHtml(event.seiscomp_oid || "")}"
            title="ხელახლა გენერაცია"
            ${event.seiscomp_oid ? "" : "disabled"}
          >
            <i class="fas fa-rotate-right"></i>
          </button>
        </td>
        <td>
          <button
            type="button"
            class="btn btn-sm btn-outline-primary open-gallery-btn"
            data-seiscomp-oid="${escapeHtml(event.seiscomp_oid)}"
            title="გალერეა"
          >
            <i class="fas fa-images"></i>
          </button>
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
  bindGalleryButtons();
  bindRegenerateButtons();
}

// /api/events-დან მონაცემების წამოღება და UI-ის განახლება.
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
  }
}

// საწყისი ჩატვირთვა.
window.getApiKey = getApiKey;
window.loadEvents = loadEvents;
loadEvents();
