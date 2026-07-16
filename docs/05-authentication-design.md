# ავთენტიფიკაციის დიზაინი (Authentication Design)

## 1. მიზანი

ავთენტიფიკაციის მოდულის მიზანია მომხმარებლების უსაფრთხო იდენტიფიკაცია, სისტემაში ავტორიზაცია, სესიის მართვა და პაროლის აღდგენის პროცესების უზრუნველყოფა.

მოდული პასუხისმგებელია მხოლოდ მომხმარებლის იდენტობის დადასტურებაზე (Authentication) და არ მოიცავს მომხმარებლის პროფილის, უფლებების (Permissions) ან მოწყობილობების (Devices) მართვას.

---

# 2. პასუხისმგებლობები

მოდული უზრუნველყოფს:

- მომხმარებლის რეგისტრაციას;
- მომხმარებლის ავტორიზაციას (Login);
- JWT Access Token-ის გენერაციას;
- Refresh Token-ის გენერაციას და განახლებას;
- სისტემიდან გამოსვლას (Logout);
- პაროლის შეცვლას;
- პაროლის აღდგენას.

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
| Authentication | JWT (JSON Web Token) |
| Password Hashing | bcrypt |
| Secure Communication | HTTPS/SSL |
| Database | MySQL |
| API | REST API |

---

# 5. Token Storage / Transport Policy

- Access Token ბრუნდება API პასუხში და იგზავნება `Authorization: Bearer <token>` header-ით;
- Refresh Token ინახება მხოლოდ `HttpOnly + Secure + SameSite=Strict` cookie-ში;
- Refresh Token არასდროს ინახება `localStorage`-ში;
- CSRF დაცვისთვის გამოიყენება `SameSite=Strict` + CSRF token შემოწმება state-changing endpoint-ებზე;
- Logout/reset password-ზე შესაბამისი refresh cookie იშლება.

---

# 6. API Endpoint-ები

## რეგისტრაცია

```http
POST /api/auth/register
```

აღწერა:

ახალი მომხმარებლის რეგისტრაცია.

Validation:

- `email` უნდა იყოს ვალიდური და უნიკალური;
- `password` მინ. 12 სიმბოლო, მინიმუმ 1 დიდი ასო, 1 პატარა ასო, 1 ციფრი, 1 სპეციალური სიმბოლო.

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

აღწერა:

ავტორიზებული მომხმარებლის პაროლის შეცვლა.

---

## პაროლის აღდგენის მოთხოვნა

```http
POST /api/auth/request_reset_password
```

აღწერა:

პაროლის აღდგენის მოთხოვნის გაგზავნა.

უსაფრთხოების წესები:

- პასუხი ყოველთვის ერთნაირია (`თუ ანგარიში არსებობს, ელ-ფოსტა გაიგზავნა`);
- Endpoint-ზე მოქმედებს IP + email rate limit;
- cooldown: ერთი მოთხოვნა 60 წამში ერთხელ.

---

## პაროლის განახლება

```http
PUT /api/auth/reset_password
```

აღწერა:

Reset Token-ის გამოყენებით ახალი პაროლის დაყენება.

წესები:

- reset token ერთჯერადია (single-use);
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

## users

| ველი | ტიპი |
|------|------|
| id | bigint |
| uuid | uuid |
| email | varchar(255) |
| password_hash | varchar(255) |
| is_active | boolean |
| last_login_at | datetime |
| created_at | datetime |
| updated_at | datetime |

---

## refresh_tokens

| ველი | ტიპი |
|------|------|
| id | bigint |
| user_id | bigint |
| jti | uuid |
| family_id | uuid |
| token_hash | varchar(255) |
| replaced_by_token_id | bigint |
| device_info | varchar(255) |
| ip_address | varchar(45) |
| expires_at | datetime |
| revoked_at | datetime |
| last_used_at | datetime |
| created_at | datetime |

---

## password_reset_tokens

| ველი | ტიპი |
|------|------|
| id | bigint |
| user_id | bigint |
| token_hash | varchar(255) |
| expires_at | datetime |
| used_at | datetime |
| created_at | datetime |

---

# 9. DB Constraints და Indexes

- `users.email` -> `UNIQUE INDEX`;
- `users.uuid` -> `UNIQUE INDEX`;
- `refresh_tokens.jti` -> `UNIQUE INDEX`;
- `refresh_tokens.user_id`, `refresh_tokens.family_id`, `refresh_tokens.expires_at` -> ინდექსები სწრაფი მოძიებისთვის;
- `password_reset_tokens.user_id`, `password_reset_tokens.expires_at` -> ინდექსები;
- ვადაგასული token-ების პერიოდული cleanup job (cron).

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
- bcrypt Password Hashing;
- HTTPS/SSL Encryption;
- Token Revocation;
- Refresh Token Rotation;
- Refresh Token Replay Detection;
- Anti-enumeration პასუხები პაროლის აღდგენაზე;
- Rate Limiting;
- CSRF დაცვა Cookie-based flow-სთვის;
- Audit Logging.

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