# API Inventory (Implemented)

ეს დოკუმენტი აღწერს **ამჟამად იმპლემენტირებულ** API-ებსა და UI-ს. დაგეგმილი ფუნქციონალი მონიშნულია ცალკე.

Base URL: `http://localhost:5000/api`  
Swagger UI: `http://localhost:5000/api/docs`

---

## Implementation Status

| მოდული | სტატუსი |
|--------|---------|
| Auth (login/register/refresh/logout/reset) | Implemented |
| Accounts (profile + user admin) | Implemented |
| Service accounts + API keys (`/api/services`) | Implemented |
| Recipients (`/api/recips`) | Implemented |
| Seismic Events (`/api/seismic_events`) | Implemented |
| Permissions models + seed + runtime checks | Implemented |
| Permissions REST catalog (list/create/delete) | Implemented |
| User permission grant/revoke on accounts | Implemented |
| Register with optional permissions | Implemented |
| `PUT /api/auth/change_password` | Planned (UI page exists) |
| `GET /api/health` | Planned |
| SeisComP ingest / Push / Redis / Celery | Planned |

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

Password policy: min 12 chars, upper + lower + digit + special. Hashing: Werkzeug.

---

## Accounts — `/api/accounts`

| Method | Path | Auth | Notes |
|--------|------|------|--------|
| GET | `/api/accounts/ourself` | JWT | Profile + flags `can_users`, `can_permissions`, `can_recips`, `can_event_view`, `can_event_edit` |
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

## Seismic Events — `/api/seismic_events`

Requires JWT or API key with **`can_event_view`** (read) and/or **`can_event_edit`** (write). Editors can also read.

| Method | Path | Auth | Notes |
|--------|------|------|--------|
| GET | `/api/seismic_events/` | `can_event_view` or `can_event_edit` | List events with nested magnitudes + beachball |
| POST | `/api/seismic_events/filter` | `can_event_view` or `can_event_edit` | Filter by body fields: `event_id` (exact), `iesdata_id`, `seiscomp_oid`, `location`, `area`, `magnitude` (code), `magnitude_min`, `magnitude_max`, `depth_min`, `depth_max`, `date_from`, `date_to`. All optional; AND combined. `iesdata_id`, `seiscomp_oid`, `location`, `area` are substring matches |
| POST | `/api/seismic_events/` | `can_event_edit` | Create. Required: `origin_time`, `latitude`, `longitude`. Optional: `depth`, `iesdata_id`, `seiscomp_oid`, `location_ge`, `location_en`, `area`, `is_automatic` (default false) |
| GET | `/api/seismic_events/<id>` | `can_event_view` or `can_event_edit` | Detail |
| PUT | `/api/seismic_events/<id>` | `can_event_edit` | Update fields |
| DELETE | `/api/seismic_events/<id>` | `can_event_edit` | Delete event + cascade magnitudes/beachball |
| GET | `/api/seismic_events/magnitude_types` | `can_event_view` or `can_event_edit` | Magnitude catalog (ML, MW, …) |
| POST | `/api/seismic_events/<id>/magnitudes` | `can_event_edit` | Add magnitude. Required: `value` + (`magnitude_id` or `magnitude_code`) |
| PUT | `/api/seismic_events/magnitudes/<em_id>` | `can_event_edit` | Update value and/or magnitude type |
| DELETE | `/api/seismic_events/magnitudes/<em_id>` | `can_event_edit` | Remove magnitude from event |
| GET | `/api/seismic_events/<id>/beachball` | `can_event_view` or `can_event_edit` | Get beachball (404 if none) |
| POST | `/api/seismic_events/<id>/beachball` | `can_event_edit` | Create beachball (one per event; 409 if exists) |
| PUT | `/api/seismic_events/<id>/beachball` | `can_event_edit` | Update `rake` / `dip` / `strike` / `beachball_path` |
| DELETE | `/api/seismic_events/<id>/beachball` | `can_event_edit` | Remove beachball |

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

Admin seed (`flask populate_db`):

- email: `roma.grigalashvili@iliauni.edu.ge`
- password: `PASSWORD` (change before production)
- all seeded permissions assigned (including `can_event_view` and `can_event_edit`)
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

---

## Web UI (server-rendered)

| Path | Purpose | Permission (navbar) |
|------|---------|---------------------|
| `/<lang>/login` | Login | Public |
| `/<lang>/accounts` | Accounts admin (+ links to Services / Permissions) | `can_users` |
| `/<lang>/registration` | Register new user (full page) | `can_users` (client-checked; API enforces) |
| `/<lang>/services` | Service registration / delete (from Accounts) | `can_users` |
| `/<lang>/permissions` | Permission catalog list/create/delete (from Accounts) | `can_permissions` only |
| `/<lang>/seismic_events` | Seismic events list + edit/delete detail | `can_event_view` / `can_event_edit` |
| `/<lang>/notify` | Recipients admin | `can_recips` |
| `/<lang>/change_password` | Change password page | Logged-in (API pending) |
| `/<lang>/reset_password/<token>` | Reset password | Public |
| `/<lang>/forgot` (or auth forgot flow) | Request reset | Public |

Registration of users happens on `/<lang>/registration` (linked from Accounts → Add user). API: `POST /api/auth/register` with optional permissions from `GET /api/permissions/`.  
Service API keys are shown once after register on the Services page.

UI strings: EN/KA via `app/static/js/i18n.js`.

---

## Code layout (API)

| Area | Files |
|------|--------|
| Auth | `app/api/auth.py`, `app/api/nsmodels/auth.py` |
| Accounts | `app/api/accounts.py`, `app/api/nsmodels/accounts.py` |
| Services | `app/api/services.py`, `app/api/nsmodels/services.py` |
| Recips | `app/api/recips.py`, `app/api/nsmodels/recips.py` |
| Seismic Events | `app/api/seismic_events.py`, `app/api/nsmodels/seismic_events.py` |
