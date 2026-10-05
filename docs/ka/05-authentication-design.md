# ავთენტიფიკაციის დიზაინი (Authentication Design)

## Implementation Status

| ფუნქცია | სტატუსი |
|---------|---------|
| Register (admin, `can_users`) | Implemented |
| Service API key auth (`X-API-Key`) | Implemented (Services module) |
| Login / Refresh / Logout / Logout all | Implemented |
| Request reset + Reset password | Implemented |
| Change password API | Planned (UI page exists) |

აქტუალური endpoint-ების სია: [`09-api-inventory.md`](09-api-inventory.md).

---

## 1. მიზანი

ავთენტიფიკაციის მოდულის მიზანია მომხმარებლების უსაფრთხო იდენტიფიკაცია, სისტემაში ავტორიზაცია, სესიის მართვა და პაროლის აღდგენის პროცესების უზრუნველყოფა.

მოდული პასუხისმგებელია მხოლოდ მომხმარებლის იდენტობის დადასტურებაზე (Authentication) და არ მოიცავს მომხმარებლის პროფილის, უფლებების (Permissions) ან მოწყობილობების (Devices) მართვას.

---

# 2. პასუხისმგებლობები

მოდული უზრუნველყოფს:

- ადმინის მიერ მომხმარებლის რეგისტრაციას (`can_users`);
- მომხმარებლის ავტორიზაციას (Login);
- JWT Access Token-ის გენერაციას;
- Refresh Token-ის გენერაციას და განახლებას;
- სისტემიდან გამოსვლას (Logout / Logout all);
- პაროლის აღდგენას (request + reset);
- პაროლის შეცვლას (planned API).

---

# 3. მოდულის ფარგლებს გარეთ

შემდეგი ფუნქციონალი არ ეკუთვნის Authentication მოდულს:

- მომხმარებლების მართვა (Accounts);
- მომხმარებლის პროფილის მართვა;
- Permissions-ის მართვა;
- Devices-ის მართვა;
- Notification Preferences;
- ადმინისტრაციული ფუნქციები.

---

# 4. გამოყენებული ტექნოლოგიები

| კომპონენტი | ტექნოლოგია |
|-----------|------------|
| Authentication | JWT (Flask-JWT-Extended) |
| Password Hashing | Werkzeug (`generate_password_hash` / `check_password_hash`) |
| Reset tokens | itsdangerous `URLSafeTimedSerializer` (signed URL, TTL 300s) |
| Secure Communication | HTTPS/SSL (production) |
| Database | SQLite (dev/test) / MySQL (production) |
| API | Flask-RESTx |

---

# 5. Token Storage / Transport Policy

- Access Token ბრუნდება API პასუხში და იგზავნება `Authorization: Bearer <token>` header-ით;
- Refresh Token ინახება მხოლოდ `HttpOnly` cookie-ში (`JWT_REFRESH_COOKIE_PATH=/api/auth`);
- Refresh Token არასდროს ინახება `localStorage`-ში (Access Token Web UI-ში `localStorage`-ში ინახება);
- Service clients იყენებენ `X-API-Key` header-ს (raw key only at registration);
- Logout/reset password-ზე შესაბამისი refresh cookie იშლება.

აქტუალური Services endpoint-ები: [`09-api-inventory.md`](09-api-inventory.md#services--apiservices).

---

# 6. API Endpoint-ები

## რეგისტრაცია

```http
POST /api/auth/register
```

Auth: JWT + `can_users` (self-register არ არის).

Body: `first_name`, `last_name`, `email`, `password`, `passwordRepeat`, optional `permission_codes` / `permissions` (array of catalog codes granted on create).

Errors:

- `email_already_registered` — ელფოსტა უკვე არსებობს;
- `validation_error` — პაროლი / ველები.

Auth: JWT **ან** service API key + `can_users`.

Validation:

- `email` უნდა იყოს ვალიდური და უნიკალური;
- `password` მინ. 6 სიმბოლო, მინიმუმ 1 დიდი ასო, 1 პატარა ასო, 1 ციფრი, 1 სპეციალური სიმბოლო;
- `password` და `passwordRepeat` უნდა ემთხვეოდეს.

---

## ავტორიზაცია

```http
POST /api/auth/login
```

აღწერა:

მომხმარებლის ავტორიზაცია ელ-ფოსტისა და პაროლის გამოყენებით.

Response:

- `access_token` (JWT)
- `expires_in` (seconds)
- `token_type` (`Bearer`)
- `refresh_token` ბრუნდება მხოლოდ Secure HttpOnly Cookie-ით

---

## Access Token-ის განახლება

```http
POST /api/auth/refresh
```

აღწერა:

ახალი Access Token-ის მიღება Refresh Token-ის გამოყენებით.

Rotation Policy:

- ყოველი წარმატებული refresh-ზე ძველი refresh token დაუყოვნებლივ ინიშნება revoked-ად;
- გენერირდება ახალი refresh token (rotation);
- თუ revoked/უკვე გამოყენებული refresh token გამოიყენეს, revoke ხდება მთელი token family (replay attack mitigation).

---

## სისტემიდან გამოსვლა

```http
POST /api/auth/logout
```

აღწერა:

აქტიური Refresh Token-ის გაუქმება.

Logout ტიპები:

- `POST /api/auth/logout` -> მხოლოდ მიმდინარე სესიის revoke;
- `POST /api/auth/logout_all` -> ყველა აქტიური სესიის revoke.

---

## პაროლის შეცვლა

```http
PUT /api/auth/change_password
```

Auth: JWT Access.

Body: `current_password`, `password`, `retype_password`.

წესები:

- მიმდინარე პაროლი სწორი უნდა იყოს;
- ახალი პაროლი უნდა ემთხვეოდეს `retype_password`-ს და პაროლის პოლიტიკას;
- ახალი პაროლი არ უნდა ემთხვეოდეს მიმდინარეს;
- წარმატებისას ყველა refresh session იშლება და cookie-ები იწმინდება (ხელახალი login).

Web UI: `/<lang>/change_password`.

---

## პაროლის აღდგენის მოთხოვნა

```http
POST /api/auth/request_reset_password
```

Body: `email`.

უსაფრთხოების წესები:

- პასუხი ყოველთვის ერთნაირია (anti-enumeration);
- cooldown: 60 წამი ერთ email-ზე, ინახება `users.last_sent_email`-ში;
- reset link იგზავნება ელ-ფოსტით (`/<lang>/reset_password/<token>`).

---

## პაროლის განახლება

```http
PUT /api/auth/reset_password
```

Body: `token`, `password`, `retype_password`.

წესები:

- token არის signed URL (itsdangerous), TTL = 300 წამი;
- ცალკე `password_reset_tokens` ცხრილი არ გამოიყენება;
- წარმატებული reset-ის შემდეგ უქმდება ყველა აქტიური refresh token.

---

# 7. API Contract (საერთო)

სავალდებულო ველიდაცია:

- ყველა request body ვალიდირდება schema-ით;
- unknown field-ები უარყოფილია (`400 bad_request`);
- token-ებთან დაკავშირებული შეცდომები ბრუნდება სტანდარტული ფორმატით:

```json
{
  "error": "token_expired",
  "message": "Access token has expired"
}
```

---

# 8. მონაცემთა მოდელი

## users (auth-relevant fields)

| ველი | ტიპი |
|------|------|
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

| ველი | ტიპი |
|------|------|
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

**არ გამოიყენება.** Reset token არის signed URL payload (user uuid + salt `reset_password`), არ ინახება ცალკე ცხრილში.

---

# 9. DB Constraints და Indexes

- `users.email` -> `UNIQUE INDEX`;
- `users.uuid` -> `UNIQUE INDEX`;
- `refresh_tokens.jti` -> `UNIQUE INDEX`;
- `refresh_tokens.user_id`, `refresh_tokens.family_id`, `refresh_tokens.expires_at` -> ინდექსები სწრაფი მოძიებისთვის;
- ვადაგასული refresh token-ების პერიოდული cleanup (planned).

---

# 10. Login პროცესი

```text
მომხმარებელი
      │
      ▼
POST /api/auth/login
      │
      ▼
მომხმარებლის მოძიება
      │
      ▼
პაროლის გადამოწმება
      │
      ▼
JWT Token-ების გენერაცია
      │
      ▼
Refresh Token-ის შენახვა
      │
      ▼
Access Token + Refresh Token
```

---

# 11. Refresh Token პროცესი

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

# 12. Logout პროცესი

```text
მომხმარებელი
      │
      ▼
POST /api/auth/logout
      │
      ▼
Refresh Token-ის გაუქმება
      │
      ▼
სესიის დასრულება
```

---

# 13. პაროლის აღდგენის პროცესი

```text
POST /api/auth/request_reset_password
                │
                ▼
Reset Token-ის გენერაცია
                │
                ▼
ელ-ფოსტის გაგზავნა
                │
                ▼
PUT /api/auth/reset_password
                │
                ▼
ახალი პაროლის შენახვა
                │
                ▼
ძველი სესიების გაუქმება
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

# 15. უსაფრთხოების მექანიზმები

- JWT Authentication;
- Werkzeug Password Hashing;
- HTTPS/SSL Encryption (production);
- Token Revocation;
- Refresh Token Rotation;
- Refresh Token Replay Detection (family revoke);
- Anti-enumeration პასუხები პაროლის აღდგენაზე;
- Email cooldown (`last_sent_email`, 60s);
- CSRF დაცვა Cookie-based flow-სთვის;
- Audit fields მომხმარებელზე (`created_by` / `updated_by`).

---

# 16. შეცდომების კოდები

| კოდი | აღწერა |
|------|---------|
| 400 | არასწორი მოთხოვნა |
| 401 | ავტორიზაცია ვერ შესრულდა |
| 403 | წვდომა აკრძალულია |
| 404 | რესურსი ვერ მოიძებნა |
| 409 | კონფლიქტი |
| 429 | მოთხოვნების რაოდენობა გადაჭარბებულია |
| 500 | სერვერის შიდა შეცდომა |

---

## Auth სპეციფიკური error codes

| error | აღწერა |
|------|---------|
| invalid_credentials | ელ-ფოსტა ან პაროლი არასწორია |
| token_expired | Token-ის ვადა ამოიწურა |
| token_revoked | Token გაუქმებულია |
| token_reused | ძველი refresh token ხელახლა იქნა გამოყენებული |
| invalid_reset_token | reset token არასწორია ან ვადაგასულია |
