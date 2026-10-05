# Notification Design

## 1. Purpose

This document describes the architecture and data models for managing recipients of earthquake and system notifications.

### Implementation Status

| Part | Status |
|------|--------|
| Recipients (`recips` + emails + numbers) | Implemented |
| Admin UI `/notify` | Implemented |
| Permission `can_recips` (write) | Implemented |
| Permission `can_recips_read` (list/detail) | Implemented |
| Service API keys for read-only access | Implemented (see Services API) |
| Alert zones (`/api/alert_zones`) | Implemented (API), see [`11-alert-zones.md`](11-alert-zones.md) |
| Push / Devices / Queue / History / Templates | Planned |

---

## 2. Architectural Approach

Notification recipients are independent of Identity users.

A recipient is a contact entity (`recip`) that can have multiple emails and multiple phone numbers.

```text
recips
  ├── recip_emails
  └── recip_numbers
```

```text
Users (Identity)
    │
    ├── can_recips → full Recips API / Notify UI
    └── can_recips_read → list/detail only (often via service API key)

Services (API keys)
    │
    └── can_recips_read (typical) → machine access to /api/recips GET

Recips (Notification contacts)
    │
    └── used later by delivery services (planned)
```

---

## 3. Module Responsibilities (implemented)

- Create / update / delete recipients;
- Add / update / delete email channels;
- Add / update / delete phone channels;
- Staff / external separation (`is_staff`);
- Soft disable on a channel or on the whole recipient (`is_active`).

---

## 4. Data Model

## recips

| Field | Type | Description |
|-------|------|-------------|
| id | int | Primary key |
| username | varchar(255) | Recipient name / description |
| is_staff | boolean | Staff member or external contact |
| is_active | boolean | Active status |
| created_at | datetime | Creation date |
| updated_at | datetime | Update date |
| created_by_user_id | int \| null | Who created it |
| updated_by_user_id | int \| null | Who updated it |

---

## recip_emails

| Field | Type | Description |
|-------|------|-------------|
| id | int | Primary key |
| recip_id | int | FK → recips.id |
| email | varchar(255) | Unique email |
| is_active | boolean | Active status |
| created_at / updated_at | datetime | Audit |
| created_by_user_id / updated_by_user_id | int \| null | Audit |

---

## recip_numbers

| Field | Type | Description |
|-------|------|-------------|
| id | int | Primary key |
| recip_id | int | FK → recips.id |
| phone_number | varchar(50) | Unique number, format `+9955XXXXXXXX` |
| is_active | boolean | Active status |
| created_at / updated_at | datetime | Audit |
| created_by_user_id / updated_by_user_id | int \| null | Audit |

Constraints:

- `recip_emails.email` → UNIQUE
- `recip_numbers.phone_number` → UNIQUE
- emails/numbers are deleted in cascade together with the recipient

---

## 5. API Endpoints

### Read (list / detail)

Required permission (any of):

```text
can_recips
can_recips_read
```

Auth: JWT Bearer **or** service `X-API-Key`.

```http
GET    /api/recips/
GET    /api/recips/{id}
```

### Write (create / update / delete + channels)

Required permission:

```text
can_recips
```

```http
POST   /api/recips/
PUT    /api/recips/{id}
DELETE /api/recips/{id}
POST   /api/recips/{id}/emails
PUT    /api/recips/emails/{email_id}
DELETE /api/recips/emails/{email_id}
POST   /api/recips/{id}/numbers
PUT    /api/recips/numbers/{number_id}
DELETE /api/recips/numbers/{number_id}
```

Create body example:

```json
{
  "username": "NSMC Duty Officer",
  "is_staff": true,
  "is_active": true
}
```

List response:

```json
{
  "items": [ { "id": 1, "username": "...", "emails": [], "numbers": [] } ],
  "total": 1
}
```

---

### Email channels

```http
POST   /api/recips/{id}/emails
PUT    /api/recips/emails/{email_id}
DELETE /api/recips/emails/{email_id}
```

```json
{ "email": "duty@example.ge", "is_active": true }
```

---

### Phone channels

```http
POST   /api/recips/{id}/numbers
PUT    /api/recips/numbers/{number_id}
DELETE /api/recips/numbers/{number_id}
```

```json
{ "phone_number": "+995599123456", "is_active": true }
```

---

## 6. Web UI

- Page: `/<lang>/notify`
- Visible in the navbar only for users with `can_recips`
- CRUD + email/phone management in modals

---

## 7. Security

- JWT Authentication **or** service API key (`X-API-Key`);
- Read: `can_recips` or `can_recips_read`;
- Write: `can_recips`;
- Email normalize/validate;
- Georgian phone normalize (`+9955XXXXXXXX`);
- Soft disable (`is_active=false`);
- Audit user ids on recipient/channel records.

---

## 8. Future Extensions (Planned)

In the next stage the Notification Module will be extended with:

- Push Notifications (FCM / APNs);
- Device Management;
- Notification History;
- Notification Templates;
- Notification Queue & Retry Mechanism;
- Automatic delivery integration with earthquake events.
