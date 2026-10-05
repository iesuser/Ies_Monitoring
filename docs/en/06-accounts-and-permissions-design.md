# Accounts and Permissions Design

## Implementation Status

| Part | Status |
|------|--------|
| Own profile GET/PUT `/api/accounts/ourself` | Implemented |
| Accounts list/detail/update/delete | Implemented (`can_users`) |
| Permission flags on profile (`can_users`, `can_recips`) | Implemented |
| Service accounts (`services` + `service_permissions`) | Implemented (`/api/services`, `/services` UI) |
| Permissions catalog REST list | Implemented (`can_permissions` or `can_users`) |
| Permissions catalog create/delete + `/permissions` UI | Implemented (`can_permissions` only) |
| Assign/revoke user permissions (`/api/accounts/<uuid>/permissions`) | Implemented |
| Register with optional permission codes | Implemented |
| Permission codes seeded | `can_users`, `can_permissions`, `can_recips`, `can_recips_read`, `can_event_view`, `can_event_edit`, `can_event_publish` |

Current endpoints: [`09-api-inventory.md`](09-api-inventory.md).

---

## 1. Purpose

This document describes the architecture, data models, API endpoints and authorization mechanisms for managing user accounts and permissions.

The system uses a **Permission-Based Authorization** model: permissions are granted directly to users, and roles (RBAC) are not used.

---

# 2. Architectural Approach

```text
User
  │
  └── Permissions
```

A user can have multiple permissions, and a permission can be held by multiple users.

```text
Users
   N
   │
   │
   ▼
user_permissions
   ▲
   │
   │
   N
Permissions
```

---

# 3. Module Responsibilities

## Accounts

- Get own profile;
- Update own profile (`first_name`, `last_name`);
- Get the list of users;
- Get user details;
- Edit a user;
- Activate / deactivate a user;
- Delete a user (when FK blockers allow it);
- Deactivating / deleting your own account is forbidden.

---

## Permissions

Implemented:

- Permission models (`permissions`, `user_permissions`);
- Runtime check via `user.check_permission(code)`;
- Seed via `flask populate_db`.

Planned (no REST API yet):

- Managing the permission list;
- Creating new permissions;
- Updating existing permissions / soft deactivate;
- Granting / revoking user permissions via the API.

---

# 4. Data Model

## users

| Field | Type | Description |
|-------|------|-------------|
| id | bigint | Primary key |
| uuid | uuid | External identifier |
| email | varchar(255) | Unique email |
| first_name | varchar(100) | First name |
| last_name | varchar(100) | Last name |
| is_active | boolean | Whether the user is active |
| created_by_user_id | bigint \| null | Who created the user (`null` for self-registration) |
| created_at | datetime | Creation date |
| updated_at | datetime | Update date |
| updated_by_user_id | bigint | Who last updated the user |

---

## permissions

| Field | Type | Description |
|-------|------|-------------|
| id | bigint | Primary key |
| code | varchar(100) | Unique code |
| name | varchar(255) | Name |
| description | text | Description |
| is_active | boolean | Whether the permission is active |
| deactivated_at | datetime \| null | When it was deactivated (soft deactivate) |
| deactivated_by_user_id | bigint \| null | Who deactivated it |
| created_by_user_id | bigint | Which user created it |
| created_at | datetime | Creation date |
| updated_at | datetime | Update date |
| updated_by_user_id | bigint | Which user last updated it |

---

## user_permissions

| Field | Type | Description |
|-------|------|-------------|
| id | bigint | Primary key |
| user_id | bigint | User |
| permission_id | bigint | Permission |
| granted_by_user_id | bigint | Which user granted it |
| granted_at | datetime | When it was granted |
| degranted_at | datetime \| null | When it was revoked (`null` = active) |
| degranted_by_user_id | bigint \| null | Who revoked it |

---

### DB Constraints and Indexes

- `users.uuid` -> `UNIQUE INDEX`;
- `users.email` -> `UNIQUE INDEX`;
- `permissions.code` -> `UNIQUE INDEX`;
- `permissions.is_active` -> index for fast filtering of active permissions;
- `user_permissions.id` -> `PRIMARY KEY`;
- `users.created_by_user_id`, `users.updated_by_user_id` -> `FOREIGN KEY -> users.id`;
- `permissions.created_by_user_id`, `permissions.updated_by_user_id` -> `FOREIGN KEY -> users.id`;
- `permissions.deactivated_by_user_id` -> `FOREIGN KEY -> users.id`;
- `user_permissions.user_id` and `user_permissions.permission_id` -> indexes for fast joins;
- `user_permissions.granted_by_user_id` -> `FOREIGN KEY -> users.id`;
- `user_permissions.degranted_by_user_id` -> `FOREIGN KEY -> users.id`;
- `user_permissions(user_id, permission_id, degranted_at)` -> index for fast lookup of active / historical records;
- Only one active record is allowed per `(user_id, permission_id)` pair at a time (enforced in the service layer + transaction);
- All `FOREIGN KEY`s must be `ON DELETE RESTRICT` (to protect history / integrity).

---

# 5. Entity Relationship Diagram

```text
users
-----
id
uuid
email
...

permissions
-----------
id
code
name
description

user_permissions
----------------
id
user_id
permission_id
granted_by_user_id
granted_at
degranted_at
degranted_by_user_id
```

```text
users
   │
   │ 1:N
   ▼
user_permissions
   ▲
   │ N:1
   │
permissions
```

---

# 6. Standard Permissions

| Code | Status | Description |
|------|--------|-------------|
| can_users | Seeded + used | Registration + accounts + services admin UI/API |
| can_permissions | Implemented | Permissions catalog CRUD + grant/revoke on accounts |
| can_recips | Seeded + used | Recipients write + Notify UI |
| can_recips_read | Seeded + used | Recipients read-only (service keys) |
| can_event_view | Implemented | View earthquake list/details/filter, magnitudes, beachball |
| can_event_edit | Implemented | Create/edit/delete earthquakes; magnitudes and beachball CRUD |
| can_event_publish | Implemented | Publish / unpublish to WordPress (JWT or service API key); details page publish panel; seismic read |


---

# 7. API Endpoints

## Own user data

### Get own profile

```http
GET /api/accounts/ourself
```

Auth: JWT.

Response includes profile fields plus boolean flags:

- `can_users`
- `can_recips`

(Computed with `check_permission`, not from a full permission list.)

---

### Update own profile

```http
PUT /api/accounts/ourself
```

Auth: JWT. Body: `first_name`, `last_name`.

---

## User management

Required permission on all admin endpoints:

```text
can_users
```

### Get the list of users

```http
GET /api/accounts/
```

Response: `{ "items": [...], "total": N }`.

---

### Get user details

```http
GET /api/accounts/{uuid}
```

---

### Update a user

```http
PUT /api/accounts/{uuid}
```

Fields: `first_name`, `last_name`, `email`, `is_active`.

Rule: a user cannot deactivate their own account.

---

### Delete a user

```http
DELETE /api/accounts/{uuid}
```

Rules:

- Deleting your own account is forbidden;
- If FK blockers prevent it (RESTRICT), a conflict/error is returned;
- On success, hard delete.

---

## Permission catalog (Implemented)

Current REST surface: [`09-api-inventory.md`](09-api-inventory.md#permissions-catalog--apipermissions).

- `GET/POST /api/permissions/` — list / create (or re-activate a soft-deleted one)
- `GET/DELETE /api/permissions/<code_or_id>` — detail / delete (unassigned → hard; assigned → soft deactivate)
- Grant on a user: `GET/POST/DELETE /api/accounts/<uuid>/permissions`
- Grant on registration: `POST /api/auth/register` + optional `permission_codes`

- `GET /api/permissions/` — list (`can_permissions` **or** `can_users`, for granting)
- `POST /api/permissions/` — create (`can_permissions` only)
- `DELETE /api/permissions/<code_or_id>` — delete (`can_permissions` only)
- UI `/permissions` — `can_permissions` only
- Grant on a user: `GET/POST/DELETE /api/accounts/<uuid>/permissions` (`can_users` or `can_permissions`)

Required permission (catalog create/delete / UI page): `can_permissions` only.

### Get the list of permissions

```http
GET /api/permissions/
```

---

### Delete / deactivate a permission

```http
DELETE /api/permissions/{code_or_id}
```

- No assignments → hard delete
- Has user/service assignments → soft deactivate (`is_active=false`); history is kept

---

### Create a new permission

```http
POST /api/permissions/
```

Body: `code`, `name`, optional `description`.

---

### Get permission details

```http
GET /api/permissions/{code_or_id}
```

---

### Update a permission

```http
PUT /api/permissions/{id}
```

Required permission:

```text
can_permissions
```

---

## User permission management (Implemented)

Partly implemented on the accounts API. Details: [`09-api-inventory.md`](09-api-inventory.md).

### Get user permissions

```http
GET /api/accounts/{uuid}/permissions
```

Required permission: `can_permissions`.

---

### Grant permissions to a user

```http
POST /api/accounts/{uuid}/permissions
```

Required permission: `can_permissions`.

Request:

```json
{
  "permission_codes": ["can_recips", "can_recips_read"]
}
```

Or `permission_ids` / `permissions`.

---

### Revoke a user permission

```http
DELETE /api/accounts/{uuid}/permissions/{permission_id}
```

Required permission:

```text
can_permissions
```


---

### Permission Lifecycle (Grant / Revoke / Re-Grant)

An active grant is defined as:

```sql
degranted_at IS NULL
```

Grant:

- If an active record already exists for the `(user_id, permission_id)` pair -> `409 already_assigned`;
- Otherwise a new record is created: `granted_at=NOW()`, `degranted_at=NULL`.

Revoke:

- The active record is found and updated: `degranted_at=NOW()`, `degranted_by_user_id=<actor_id>`;
- If no active record exists -> `404 not_assigned` (or idempotent `200`, by API agreement).

Re-Grant (granting again after a revoke):

- The old record is neither deleted nor overwritten;
- A new record is created with a new `granted_at`, so the history is fully preserved.

Permission assignment security rules:

- A user with `can_permissions` can grant/revoke any permission on any user;
- `can_permissions` is a platform administration permission and is granted only to trusted administrators;
- The operation runs in a transaction to avoid race conditions.

---

## API Contract (common rules)

- The accounts list currently returns `{ items, total }` (pagination query params — planned);
- All errors are returned in a single format:

```json
{
  "error": "forbidden",
  "message": "Missing required permission: can_users"
}
```

- Standard authz errors: `forbidden`, `permission_denied`, `validation_error`, `conflict`, `not_found`, `already_assigned`, `not_assigned`.

---

# 8. Authorization Flow

```text
Request
   │
   ▼
JWT Validation
   │
   ▼
User Lookup
   │
   ▼
Load User Permissions
   │
   ▼
Permission Check
   │
   ├── Allowed
   └── Forbidden
```

---

# 9. Permission Validation

```python
@jwt_required()
@permission_required("can_users")
def get_accounts():
    ...
```

---

# 10. JWT Payload

```json
{
  "sub": "user_uuid",
  "jti": "token_uuid",
  "iat": 1750000000,
  "exp": 1750003600
}
```

Permissions are not stored in the JWT; they are loaded from the database or Redis cache on every request.

---

# 11. Security Mechanisms

- JWT Authentication;
- Permission-Based Authorization;
- HTTPS/SSL;
- Rate Limiting;
- Audit Logging;
- User deactivation (`is_active=false`);
- Centralized Permission Validation;
- Centralized Permission Governance based on `can_permissions`.

---

# 12. Audit Logging

The system records:

- User creation;
- User updates;
- User deactivation;
- Permission creation;
- Permission updates;
- Permission grants;
- Permission revocations;
- Permission deactivation.

Each audit record contains at least:

- `event_type` (e.g. `permission_assigned`);
- `actor_user_id` (who performed it);
- `target_user_id` or `target_resource_id` (on whom / what it was performed);
- `changes` (before/after snapshot or diff);
- `ip_address`, `user_agent`;
- `request_id` (for traceability);
- `created_at`.

---
