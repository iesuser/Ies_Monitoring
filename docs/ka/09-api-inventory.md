# API Inventory (Implemented)

ეს დოკუმენტი აღწერს **ამჟამად იმპლემენტირებულ** API-ებსა და UI-ს. დაგეგმილი ფუნქციონალი მონიშნულია ცალკე.

Base URL: `http://localhost:5000/api`  
Swagger UI: `http://localhost:5000/docs/`

Flask-RESTX mounting: `Api` has no URL `prefix`; each namespace uses `path="/api"` and resource routes include the segment (e.g. `/auth/login`, `/seismic_events/`). Public paths stay `/api/...`.

---

## Implementation Status

| მოდული | სტატუსი |
|--------|---------|
| Auth (login/register/refresh/logout/reset) | Implemented |
| Accounts (profile + user admin) | Implemented |
| Service accounts + API keys (`/api/services`) | Implemented |
| Recipients (`/api/recips`) | Implemented |
| Seismic Events (`/api/seismic_events`) | Implemented |
| Publish Events (`/api/publish_events`) | Implemented |
| Alert Zones (`/api/alert_zones`) | Implemented |
| Permissions models + seed + runtime checks | Implemented |
| Permissions REST catalog (list/create/delete) | Implemented |
| User permission grant/revoke on accounts | Implemented |
| Register with optional permissions | Implemented |
| `PUT /api/auth/change_password` | Implemented |
| `GET /api/health` | Planned |
| SeisComP ingest / Push / Redis / Celery | Planned |

Seismic Events UI/API დეტალური აღწერა: [`10-seismic-events.md`](10-seismic-events.md).

---

## Authentication methods

| მეთოდი | Header / Cookie | გამოყენება |
|--------|-----------------|------------|
| JWT Access | `Authorization: Bearer <token>` | Web UI და მომხმარებლის API |
| JWT Refresh | HttpOnly cookie (`path=/api/auth`) | მხოლოდ `/api/auth/refresh` |
| Service API Key | `X-API-Key: ies_...` | Service accounts; უფლებები `service_permissions`-იდან |

ბევრი admin endpoint მხარდაჭერილია **JWT ან API key**-ით (`require_permissions`).

---

## Auth — `/api/auth`

| Method | Path | Auth | Notes |
|--------|------|------|--------|
| POST | `/api/auth/register` | JWT/API key + `can_users` | Admin creates users. Body: `first_name`, `last_name`, `email`, `password`, `passwordRepeat`, optional `permission_codes` / `permissions`. Granting codes on create also requires **`can_permissions`**. Error `email_already_registered` if email exists |
| POST | `/api/auth/login` | Public | `access_token`, `token_type`, `expires_in`. Refresh in HttpOnly cookie |
| POST | `/api/auth/refresh` | Refresh cookie | Rotation + family revoke on reuse |
| POST | `/api/auth/logout` | Optional | Revokes current session; clears cookies |
| POST | `/api/auth/logout_all` | JWT | All sessions; response has `revoked_sessions` |
| POST | `/api/auth/request_reset_password` | Public | Body: `email`. 60s cooldown (`users.last_sent_email`) |
| PUT | `/api/auth/reset_password` | Public | Body: `token`, `password`, `retype_password`. itsdangerous URL token, TTL 300s |
| PUT | `/api/auth/change_password` | JWT | Body: `current_password`, `password`, `retype_password`. Validates policy; revokes all refresh sessions and clears cookies |

Password policy: min 6 chars, upper + lower + digit + special. Hashing: Werkzeug.

---

## Accounts — `/api/accounts`

| Method | Path | Auth | Notes |
|--------|------|------|--------|
| GET | `/api/accounts/ourself` | JWT | Profile + flags `can_users`, `can_permissions`, `can_recips`, `can_event_view`, `can_event_edit`, `can_event_publish` |
| PUT | `/api/accounts/ourself` | JWT | Own `first_name`, `last_name` |
| GET | `/api/accounts/` | JWT/API key + `can_users` | `{ items, total }` |
| GET | `/api/accounts/<uuid>` | JWT/API key + `can_users` | Single user |
| PUT | `/api/accounts/<uuid>` | JWT/API key + `can_users` | `first_name`, `last_name`, `email`, `is_active`. Cannot deactivate self |
| DELETE | `/api/accounts/<uuid>` | JWT/API key + `can_users` | Hard delete when FK allows. Cannot delete self |

### User permission assignment

| Method | Path | Auth | Notes |
|--------|------|------|--------|
| GET | `/api/accounts/<uuid>/permissions` | JWT/API key + **`can_permissions`** | User's active permissions |
| POST | `/api/accounts/<uuid>/permissions` | **`can_permissions`** | Grant. Body: `permission_codes` and/or `permission_ids` (or `permissions` codes array). Soft history: re-grant creates new row |
| DELETE | `/api/accounts/<uuid>/permissions/<code>` | **`can_permissions`** | Soft revoke (`degranted_at`). Cannot revoke own `can_users` / `can_permissions` |

GET `/api/accounts/<uuid>` also returns `permissions: ["can_recips", ...]` for active codes when the caller has `can_users`.

---

## Permissions catalog — `/api/permissions`

Catalog management is separate from user assignment.

| Method | Path | Auth | Notes |
|--------|------|------|--------|
| GET | `/api/permissions/` | JWT/API key + `can_permissions` **or** `can_users` | Catalog list (assignment UI needs `can_permissions` to grant; list readable by `can_users` if needed). `{ items, total }` |
| POST | `/api/permissions/` | JWT/API key + `can_permissions` | Create. Body: `code`, `name`, optional `description`. Re-activates soft-deleted same `code` (200). Conflict if active duplicate (409) |
| GET | `/api/permissions/<code_or_id>` | `can_permissions` or `can_users` | Single permission by code or numeric id |
| DELETE | `/api/permissions/<code_or_id>` | `can_permissions` | Hard delete if unassigned; otherwise soft-deactivate (`is_active=false`) while referenced |

UI: `/permissions` page, catalog create/delete, and **user permission assignment** all require `can_permissions`. `can_users` alone can edit accounts but cannot grant/revoke codes.

---

## Services — `/api/services`

Service accounts hold hashed API keys and assigned permissions (`service_permissions`).

| Method | Path | Auth | Notes |
|--------|------|------|--------|
| GET | `/api/services/` | JWT/API key + `can_users` | List services + active permission codes |
| POST | `/api/services/` | JWT/API key + `can_users` | Register service. Body: `name`, optional `description`, `permissions` (array of codes). Returns **one-time** `api_key` |
| DELETE | `/api/services/<uuid>` | JWT/API key + `can_users` | Delete service + permission assignments |

Raw API key is shown only once at registration (`api_key_hash` is stored).

---

## Recipients — `/api/recips`

| Method | Path | Auth | Notes |
|--------|------|------|--------|
| GET | `/api/recips/` | JWT/API key + `can_recips` **or** `can_recips_read` | List with nested emails/numbers |
| GET | `/api/recips/<id>` | same | Detail |
| POST | `/api/recips/` | JWT/API key + `can_recips` | Create |
| PUT | `/api/recips/<id>` | `can_recips` | Update |
| DELETE | `/api/recips/<id>` | `can_recips` | Delete + cascade channels |
| POST | `/api/recips/<id>/emails` | `can_recips` | Add email |
| PUT | `/api/recips/emails/<email_id>` | `can_recips` | Update email |
| DELETE | `/api/recips/emails/<email_id>` | `can_recips` | Remove email |
| POST | `/api/recips/<id>/numbers` | `can_recips` | Add phone (`+9955XXXXXXXX`) |
| PUT | `/api/recips/numbers/<number_id>` | `can_recips` | Update phone |
| DELETE | `/api/recips/numbers/<number_id>` | `can_recips` | Remove phone |

---

## Alert Zones — `/api/alert_zones`

დეტალური აღწერა: [`11-alert-zones.md`](11-alert-zones.md).

| Method | Path | Auth | Notes |
|--------|------|------|--------|
| GET | `/api/alert_zones` | JWT/API key + `can_recips` **or** `can_recips_read` | List zones |
| GET | `/api/alert_zones/<id>` | same | Detail |
| POST | `/api/alert_zones` | JWT/API key + `can_recips` | Create. Required: `name`, `geometry` (GeoJSON Polygon, `[lon, lat]`), `min_magnitude` (ML, 0–10), `notif_channels` (non-empty subset of `mail`, `number`, `push_notif`). Optional: `max_magnitude` (0–10, ≥ `min_magnitude`; null = no upper limit), `enabled` (default true), `notif_is_staff` (default false). Unclosed rings are closed automatically |
| PUT | `/api/alert_zones/<id>` | `can_recips` | Partial update: only provided fields change |
| DELETE | `/api/alert_zones/<id>` | `can_recips` | Delete |

---

## Seismic Events — `/api/seismic_events`

Requires JWT or API key with **`can_event_view`**, **`can_event_edit`**, or **`can_event_publish`** for read endpoints. Write endpoints require **`can_event_edit`**. Editors and publishers can also read.

| Method | Path | Auth | Notes |
|--------|------|------|--------|
| GET | `/api/seismic_events/` | `can_event_view` / `can_event_edit` / `can_event_publish` | List events with nested magnitudes + beachball; payload includes `is_published`, `published_at` |
| POST | `/api/seismic_events/filter` | `can_event_view` / `can_event_edit` / `can_event_publish` | Filter by body fields: `event_id` (exact), `event_query` (substring on id or iesdata_id), `iesdata_id`, `seiscomp_oid`, `location`, `area`, `magnitude` (code), `magnitude_min`, `magnitude_max`, `magnitudes` (list of `{magnitude, magnitude_min, magnitude_max}` for AND), `depth_min`, `depth_max`, `date_from`, `date_to`. All optional; AND combined. `iesdata_id`, `seiscomp_oid`, `location`, `area` are substring matches |
| POST | `/api/seismic_events/` | `can_event_edit` | Create. Required: `origin_time`, `latitude`, `longitude`. Optional: `depth`, `iesdata_id`, `seiscomp_oid`, `location_ge`, `location_en`, `area`, `is_automatic` (default false). **UI also requires `depth`.** |
| GET | `/api/seismic_events/<id>` | `can_event_view` / `can_event_edit` / `can_event_publish` | Detail (includes `is_published`, `published_at`) |
| PUT | `/api/seismic_events/<id>` | `can_event_edit` | Update fields |
| DELETE | `/api/seismic_events/<id>` | `can_event_edit` | Delete event + cascade magnitudes/beachball |
| GET | `/api/seismic_events/magnitude_types` | `can_event_view` / `can_event_edit` / `can_event_publish` | Magnitude catalog (ML, MW, …) |
| POST | `/api/seismic_events/<id>/magnitudes` | `can_event_edit` | Add magnitude. Required: `value` + (`magnitude_id` or `magnitude_code`) |
| PUT | `/api/seismic_events/magnitudes/<em_id>` | `can_event_edit` | Update value and/or magnitude type |
| DELETE | `/api/seismic_events/magnitudes/<em_id>` | `can_event_edit` | Remove magnitude from event |
| GET | `/api/seismic_events/<id>/beachball` | `can_event_view` / `can_event_edit` / `can_event_publish` | Get beachball (404 if none) |
| POST | `/api/seismic_events/<id>/beachball` | `can_event_edit` | Create beachball (one per event; 409 if exists). `strike`/`dip`/`rake` must be **all three or none**. When all three are set, generates `/static/beachballs/beachball_<id>.png` and stores path (client `beachball_path` ignored) |
| PUT | `/api/seismic_events/<id>/beachball` | `can_event_edit` | Update mechanism: `strike`/`dip`/`rake` must be **all three or none**; regenerates PNG when all three present |
| DELETE | `/api/seismic_events/<id>/beachball` | `can_event_edit` | Remove beachball row and generated PNG |

---

## Publish Events — `/api/publish_events`

Publish/unpublish require JWT or API key with **`can_event_publish`**. List is public.

| Method | Path | Auth | Notes |
|--------|------|------|--------|
| GET | `/api/publish_events/` | Public (no auth) | List all published events (`items` + `total`), newest `published_at` first; each item includes nested seismic `event` |
| POST | `/api/publish_events/publish/<id>` | `can_event_publish` | Publish/update on WordPress (no body). WP `id` = our event id; `type` = `A`/`M` from `is_automatic`; `description_*` and `region_*` both from `location_*`; mag prefers ML. Upserts `published_events` |
| POST | `/api/publish_events/unpublish/<id>` | `can_event_publish` | Unpublish from WordPress and delete `published_events` row |

---

## Seeded permissions

| Code | Usage |
|------|--------|
| `can_users` | Register users, accounts admin, services; read catalog list |
| `can_permissions` | Permissions page, catalog create/delete, grant/revoke on users (and on register) |
| `can_recips` | Full recipients write + Notify UI |
| `can_recips_read` | Read-only recipients (typical for service API keys) |
| `can_event_view` | View seismic events, magnitudes, beachballs |
| `can_event_edit` | Create/update/delete seismic events, magnitudes, beachballs |
| `can_event_publish` | Publish/unpublish seismic events to WordPress (JWT or service API key); also allows read of seismic events for the details publish UI |

Admin seed (`flask populate_db`):

- email: `roma.grigalashvili@iliauni.edu.ge`
- password: `PASSWORD` (change before production)
- all seeded permissions assigned (including `can_event_view`, `can_event_edit`, `can_event_publish`)
- magnitude catalog: ML, MB, MS, MD, MW, K, MPV, MLH, MC, MLV, M

---

## Implemented data models

| Table | Purpose |
|-------|---------|
| `users` | Identity users |
| `permissions` | Permission catalog |
| `user_permissions` | User ↔ permission grants (with degrant history) |
| `refresh_tokens` | Refresh token sessions / rotation |
| `services` | Service accounts + API key hash/prefix |
| `service_permissions` | Service ↔ permission grants |
| `recips` | Notification recipients |
| `recip_emails` | Recipient emails |
| `recip_numbers` | Recipient phones |
| `seismic_events` | Earthquake events |
| `magnitudes` | Magnitude type catalog |
| `event_magnitudes` | Event ↔ magnitude values |
| `event_beachball` | Focal mechanism / beachball (0..1 per event) |
| `published_events` | WordPress publish state (0..1 per seismic event) |

---

## Web UI (server-rendered)

| Path | Purpose | Permission (navbar) |
|------|---------|---------------------|
| `/<lang>/login` | Login | Public |
| `/<lang>/accounts` | Accounts admin (+ links to Services / Permissions) | `can_users` |
| `/<lang>/registration` | Register new user (full page) | `can_users` (client-checked; API enforces) |
| `/<lang>/services` | Service registration / delete (from Accounts) | `can_users` |
| `/<lang>/permissions` | Permission catalog list/create/delete (from Accounts) | `can_permissions` only |
| `/<lang>/seismic_events` | Seismic events list, map, filters, create/edit modals | `can_event_view` / `can_event_edit` / `can_event_publish` |
| `/<lang>/seismic_events/<id>` | Event details (summary, publish panel, Overview / Magnitudes / Beachball / Map) | `can_event_view` / `can_event_edit` / `can_event_publish` |
| `/<lang>/notify` | Recipients admin | `can_recips` |
| `/<lang>/change_password` | Change password page | Logged-in (JWT; API implemented) |
| `/<lang>/reset_password/<token>` | Reset password | Public |
| `/<lang>/forgot` (or auth forgot flow) | Request reset | Public |

Registration of users happens on `/<lang>/registration` (linked from Accounts → Add user). API: `POST /api/auth/register` with optional permissions from `GET /api/permissions/`.  
Service API keys are shown once after register on the Services page.

UI strings: EN/KA via `app/static/js/i18n.js`.

### Seismic Events UI notes

- List filtering is **server-side** (`GET /` when empty, `POST /filter` when criteria set) — see [`10-seismic-events.md`](10-seismic-events.md).
- Origin time in UI is plain text (`YYYY-MM-DD HH:mm:ss` / ISO); displayed as `YYYY-MM-DDTHH:mm:ss` without client timezone shift.
- Filter dates use Flatpickr `dd/mm/yyyy`.
- Beachball `strike`/`dip`/`rake`: UI validates all-three-or-none before submit (same rule as API).
- Details page Edit opens the edit modal in-place (does not redirect to the list).
- Details page **publish panel** (below summary): shows published / not published, optional `published_at`, and Publish / Update publish / Unpublish when the user has `can_event_publish`. Calls `POST /api/publish_events/publish|unpublish/<id>`. Event must have at least one magnitude before publish.

---

## Code layout (API)

| Area | Files |
|------|--------|
| Auth | `app/api/auth.py`, `app/api/nsmodels/auth.py` |
| Accounts | `app/api/accounts.py`, `app/api/nsmodels/accounts.py` |
| Services | `app/api/services.py`, `app/api/nsmodels/services.py` |
| Recips | `app/api/recips.py`, `app/api/nsmodels/recips.py` |
| Seismic Events | `app/api/seismic_events.py`, `app/api/nsmodels/seismic_events.py`, `app/utils/gen_beachball_img.py` |
| Publish Events | `app/api/publish_events.py`, `app/api/nsmodels/publish_events.py`, `app/utils/wp_publish_client.py` |
