# Seismic Events — Design & UI (Implemented)

This document describes the **implemented** Seismic Events module: API behavior, the Web UI and client flows.  
Short API endpoint table: [`09-api-inventory.md`](09-api-inventory.md).

---

## 1. Permissions

| Code | UI / API |
|------|----------|
| `can_event_view` | View the list, filter, details and beachball/magnitudes |
| `can_event_edit` | Create, edit, delete; magnitude and beachball CRUD |
| `can_event_publish` | WordPress publish / unpublish (API + details page publish panel); also grants seismic read |

`can_event_edit` also grants read access. Publishing is a separate permission (`can_event_publish`).

Navbar → Events is visible if the user has any of these permissions.

---

## 2. Web UI Pages

| Path | Description |
|------|-------------|
| `/<lang>/seismic_events` | List, map (Leaflet), filters, create/edit modals |
| `/<lang>/seismic_events/<id>` | Event details — summary banner, publish panel, tabs |

i18n: EN/KA (`app/static/js/i18n.js`).

### 2.1 List (`events.html`)

- **Map + filters** at the top; earthquake table below.
- **Table columns:** Action · Earthquake Time · Magnitude · Location (`location_en` in EN, `location_ge` in KA).
- **Actions:** Details · Edit · Delete (Edit/Delete for `can_event_edit`).
- The Details button navigates to `/seismic_events/<id>`.
- **Add Earthquake** — `can_event_edit` only.

### 2.2 Filtering (server-side)

The client **does not filter** the full list in the browser. Apply / Reset call the API:

| State | Request |
|-------|---------|
| Empty filter / Reset | `GET /api/seismic_events/` |
| Active filter | `POST /api/seismic_events/filter` |

Filter fields and API mapping:

| UI field | API body |
|----------|----------|
| Event ID | `event_query` (substring on id **or** `iesdata_id`) |
| SeisComP OID | `seiscomp_oid` |
| Location | `location` (`location_en` / `location_ge`) |
| Area | `area` |
| Magnitude rows | One row → `magnitude` / `magnitude_min` / `magnitude_max`; several → `magnitudes: [{…}]` (AND) |
| Depth min/max | `depth_min` / `depth_max` |
| Date from/to | `date_from` / `date_to` (ISO 8601) |

Date UI: Flatpickr, format **`dd/mm/yyyy`**.

After create/edit/delete the list is reloaded with the active filter.

### 2.3 Create / Edit (modals)

Field order:

1. IES data ID · SeisComP OID  
2. Origin Time (ISO 8601) * · Depth (km) *  
3. Latitude * · Longitude *  
4. Location GE · Location EN · Area  
5. Magnitudes  
6. Beachball (Strike · Dip · Rake)

**Origin time (UI):** text field; paste/save **without timezone shift**.

Accepted formats:

- `YYYY-MM-DD HH:mm:ss` → stored as `YYYY-MM-DDTHH:mm:ss`
- `YYYY-MM-DDTHH:mm:ss`
- `dd/mm/yyyy, HH:mm:ss` (also supported)

In the table and on details the time is shown as **`YYYY-MM-DDTHH:mm:ss`**.

**Beachball UI validation:** `strike`, `dip`, `rake` must be either all filled or all empty. On partial input the modal shows a **warning** and submit does not proceed.

On create, a filled beachball is sent with `POST .../beachball` after the event is created.  
On edit — `POST` (if there was none) or `PUT` (if it existed); deletion via a separate button.

### 2.4 Event details (`eventDetails.html`)

Structure:

1. Back + title + Edit/Delete (`can_event_edit`)
2. **Summary banner** — Origin time, Magnitude, Depth, Lat/Lon, Event ID + OID / IES meta
3. **Publish panel** (below the summary) — publish status and actions
4. **Tabs:**
   - Overview — full metadata
   - Magnitudes — table
   - Beachball — PNG + strike/dip/rake
   - Map — Leaflet, single event marker

Edit opens in a **modal on the same page** (does not go to the list). After saving, the details refresh in place.  
Delete → back to the list.

#### Publish panel (`can_event_publish`)

- Status: **Published** / **Not published** (+ `published_at` if published).
- If unpublished: **Publish**.
- If already published: **Update publish** + **Unpublish**.
- API:
  - `POST /api/publish_events/publish/<id>`
  - `POST /api/publish_events/unpublish/<id>`
- Before publishing, the event needs at least one magnitude (API returns 400 otherwise).
- After success the UI receives the updated `event` (`is_published`, `published_at`) and re-renders the panel.

---

## 3. API Behavior (details)

### 3.1 Create / Update event

| Field | Create API | UI |
|-------|------------|-----|
| `origin_time` | required | required |
| `latitude`, `longitude` | required | required |
| `depth` | optional | required (UI) |
| `iesdata_id`, `seiscomp_oid`, locations, `area` | optional | optional |
| `is_automatic` | optional (default false) | not changed from the UI on create |

Event JSON also contains `is_published` and `published_at` (from the `published_events` relationship).

### 3.2 Filter

All fields optional; conditions are **AND**.  
`date_from` / `date_to` — ISO 8601 datetime.  
Multiple magnitude criteria — `magnitudes` list, one EXISTS subquery each (AND).

### 3.3 Beachball

- At most one record per event.
- `strike` / `dip` / `rake`: **all three or none** (API 400 if partial).
- When all three are present the server generates a PNG (`ObsPy beachball`) →  
  `/static/beachballs/beachball_<event_id>.png` and stores it in `beachball_path`.
- A `beachball_path` sent by the client is **ignored**.

Generation: `app/utils/gen_beachball_img.py`.

### 3.4 Publish / Unpublish (WordPress)

Details: [`09-api-inventory.md`](09-api-inventory.md) — Publish Events.  
Client: `app/utils/wp_publish_client.py`. Config: `WP_PUBLISH_CODE` (and the WP URL in env/config).

---

## 4. Frontend Files

| File | Role |
|------|------|
| `app/views/seismic_events/routes.py` | `/seismic_events`, `/seismic_events/<id>` |
| `app/templates/seismic_events/events.html` | List + map |
| `app/templates/seismic_events/eventDetails.html` | Details (summary, publish panel, tabs) |
| `app/templates/seismic_events/filterEvent.html` | Filter form |
| `app/templates/seismic_events/createEvent.html` | Create modal |
| `app/templates/seismic_events/editEvent.html` | Edit modal |
| `app/static/js/seismic_events/events.js` | List, auth, filter apply orchestration |
| `app/static/js/seismic_events/filterEvent.js` | Filter state → API payload |
| `app/static/js/seismic_events/createEvent.js` | Create + magnitudes + beachball |
| `app/static/js/seismic_events/editEvent.js` | Edit + magnitudes + beachball |
| `app/static/js/seismic_events/eventDetailsPage.js` | Details page + publish panel |
| `app/static/js/seismic_events/eventDetail.js` | Actions: details button + Event ID link |
| `app/static/js/seismic_events/map.js` | List Leaflet map |
| `app/static/js/seismic_events/deleteEvent.js` | Delete from the list |
| `app/static/css/styles.css` | Summary / publish panel styles |

API: `app/api/seismic_events.py`, `app/api/nsmodels/seismic_events.py`,  
`app/api/publish_events.py`, `app/api/nsmodels/publish_events.py`  
Models: `seismic_events`, `magnitudes`, `event_magnitudes`, `event_beachball`, `published_events`

---

## 5. Tests

`tests/test_seismic_events_api.py` — CRUD, filter, beachball all-or-none, PNG path, etc.  
`tests/test_publish_events_api.py` — publish / unpublish / public list.

```bash
pytest tests/test_seismic_events_api.py tests/test_publish_events_api.py -q
```
