# Authentication Design

## Implementation Status

| Feature | Status |
|---------|--------|
| Register (admin, `can_users`) | Implemented |
| Service API key auth (`X-API-Key`) | Implemented (Services module) |
| Login / Refresh / Logout / Logout all | Implemented |
| Request reset + Reset password | Implemented |
| Change password API | Planned (UI page exists) |

Current endpoint list: [`09-api-inventory.md`](09-api-inventory.md).

---

## 1. Purpose

The authentication module provides secure user identification, login, session management and password recovery.

The module is responsible only for verifying user identity (Authentication). It does not cover user profile, permission or device management.

---

# 2. Responsibilities

The module provides:

- User registration by an admin (`can_users`);
- User login;
- JWT Access Token generation;
- Refresh Token generation and renewal;
- Logout (Logout / Logout all);
- Password recovery (request + reset);
- Password change (planned API).

---

# 3. Out of Scope

The following functionality does not belong to the Authentication module:

- User management (Accounts);
- User profile management;
- Permission management;
- Device management;
- Notification Preferences;
- Administrative functions.

---

# 4. Technologies

| Component | Technology |
|-----------|------------|
| Authentication | JWT (Flask-JWT-Extended) |
| Password Hashing | Werkzeug (`generate_password_hash` / `check_password_hash`) |
| Reset tokens | itsdangerous `URLSafeTimedSerializer` (signed URL, TTL 300s) |
| Secure Communication | HTTPS/SSL (production) |
| Database | SQLite (dev/test) / MySQL (production) |
| API | Flask-RESTx |

---

# 5. Token Storage / Transport Policy

- The Access Token is returned in the API response and sent in the `Authorization: Bearer <token>` header;
- The Refresh Token is stored only in an `HttpOnly` cookie (`JWT_REFRESH_COOKIE_PATH=/api/auth`);
- The Refresh Token is never stored in `localStorage` (the Web UI stores the Access Token in `localStorage`);
- Service clients use the `X-API-Key` header (raw key only at registration);
- On logout / password reset the corresponding refresh cookie is cleared.

Current Services endpoints: [`09-api-inventory.md`](09-api-inventory.md#services--apiservices).

---

# 6. API Endpoints

## Registration

```http
POST /api/auth/register
```

Auth: JWT + `can_users` (no self-registration).

Body: `first_name`, `last_name`, `email`, `password`, `passwordRepeat`, optional `permission_codes` / `permissions` (array of catalog codes granted on create).

Errors:

- `email_already_registered` — the email already exists;
- `validation_error` — password / fields.

Auth: JWT **or** service API key + `can_users`.

Validation:

- `email` must be valid and unique;
- `password` min. 6 characters, at least 1 uppercase letter, 1 lowercase letter, 1 digit, 1 special character;
- `password` and `passwordRepeat` must match.

---

## Login

```http
POST /api/auth/login
```

Description:

Logs the user in with email and password.

Response:

- `access_token` (JWT)
- `expires_in` (seconds)
- `token_type` (`Bearer`)
- `refresh_token` is returned only as a Secure HttpOnly cookie

---

## Access Token refresh

```http
POST /api/auth/refresh
```

Description:

Gets a new Access Token using the Refresh Token.

Rotation Policy:

- On every successful refresh the old refresh token is immediately marked as revoked;
- A new refresh token is generated (rotation);
- If a revoked / already used refresh token is presented, the whole token family is revoked (replay attack mitigation).

---

## Logout

```http
POST /api/auth/logout
```

Description:

Revokes the active Refresh Token.

Logout types:

- `POST /api/auth/logout` -> revokes only the current session;
- `POST /api/auth/logout_all` -> revokes all active sessions.

---

## Change password

```http
PUT /api/auth/change_password
```

Auth: JWT Access.

Body: `current_password`, `password`, `retype_password`.

Rules:

- The current password must be correct;
- The new password must match `retype_password` and the password policy;
- The new password must differ from the current one;
- On success all refresh sessions are removed and cookies are cleared (login again).

Web UI: `/<lang>/change_password`.

---

## Password reset request

```http
POST /api/auth/request_reset_password
```

Body: `email`.

Security rules:

- The response is always the same (anti-enumeration);
- Cooldown: 60 seconds per email, stored in `users.last_sent_email`;
- The reset link is sent by email (`/<lang>/reset_password/<token>`).

---

## Password reset

```http
PUT /api/auth/reset_password
```

Body: `token`, `password`, `retype_password`.

Rules:

- The token is a signed URL (itsdangerous), TTL = 300 seconds;
- No separate `password_reset_tokens` table is used;
- After a successful reset all active refresh tokens are revoked.

---

# 7. API Contract (common)

Mandatory validation:

- Every request body is validated against a schema;
- Unknown fields are rejected (`400 bad_request`);
- Token-related errors are returned in a standard format:

```json
{
  "error": "token_expired",
  "message": "Access token has expired"
}
```

---

# 8. Data Model

## users (auth-relevant fields)

| Field | Type |
|-------|------|
| id | int |
| uuid | string(36) |
| first_name / last_name | varchar(100) |
| email | varchar(255) |
| password_hash | varchar(255) |
| is_active | boolean |
| last_login_at | datetime \| null |
| last_sent_email | datetime \| null |
| created_at / updated_at | datetime |
| created_by_user_id / updated_by_user_id | int \| null |

---

## refresh_tokens

| Field | Type |
|-------|------|
| id | int |
| user_id | int |
| jti | uuid |
| family_id | uuid |
| token_hash | varchar(255) |
| replaced_by_token_id | int \| null |
| device_info | varchar(255) |
| ip_address | varchar(45) |
| expires_at | datetime |
| revoked_at | datetime \| null |
| last_used_at | datetime \| null |
| created_at | datetime |

---

## password_reset_tokens

**Not used.** The reset token is a signed URL payload (user uuid + salt `reset_password`) and is not stored in a separate table.

---

# 9. DB Constraints and Indexes

- `users.email` -> `UNIQUE INDEX`;
- `users.uuid` -> `UNIQUE INDEX`;
- `refresh_tokens.jti` -> `UNIQUE INDEX`;
- `refresh_tokens.user_id`, `refresh_tokens.family_id`, `refresh_tokens.expires_at` -> indexes for fast lookup;
- Periodic cleanup of expired refresh tokens (planned).

---

# 10. Login Flow

```text
User
      │
      ▼
POST /api/auth/login
      │
      ▼
Look up user
      │
      ▼
Verify password
      │
      ▼
Generate JWT tokens
      │
      ▼
Store Refresh Token
      │
      ▼
Access Token + Refresh Token
```

---

# 11. Refresh Token Flow

```text
Access Token Expired
          │
          ▼
POST /api/auth/refresh
          │
          ▼
Refresh Token Validation
          │
          ▼
Old Refresh Token Revoked
          │
          ▼
New Access Token + New Refresh Token
```

---

# 12. Logout Flow

```text
User
      │
      ▼
POST /api/auth/logout
      │
      ▼
Revoke Refresh Token
      │
      ▼
End session
```

---

# 13. Password Recovery Flow

```text
POST /api/auth/request_reset_password
                │
                ▼
Generate Reset Token
                │
                ▼
Send email
                │
                ▼
PUT /api/auth/reset_password
                │
                ▼
Store new password
                │
                ▼
Revoke old sessions
```

---

# 14. JWT Payload

```json
{
  "sub": "user_uuid",
  "jti": "token_uuid",
  "type": "access",
  "iat": 1750000000,
  "exp": 1750000000
}
```

---

# 15. Security Mechanisms

- JWT Authentication;
- Werkzeug Password Hashing;
- HTTPS/SSL Encryption (production);
- Token Revocation;
- Refresh Token Rotation;
- Refresh Token Replay Detection (family revoke);
- Anti-enumeration responses on password recovery;
- Email cooldown (`last_sent_email`, 60s);
- CSRF protection for the cookie-based flow;
- Audit fields on users (`created_by` / `updated_by`).

---

# 16. Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad request |
| 401 | Authentication failed |
| 403 | Access forbidden |
| 404 | Resource not found |
| 409 | Conflict |
| 429 | Too many requests |
| 500 | Internal server error |

---

## Auth-specific error codes

| error | Description |
|-------|-------------|
| invalid_credentials | Email or password is incorrect |
| token_expired | Token has expired |
| token_revoked | Token has been revoked |
| token_reused | An old refresh token was reused |
| invalid_reset_token | Reset token is invalid or expired |
