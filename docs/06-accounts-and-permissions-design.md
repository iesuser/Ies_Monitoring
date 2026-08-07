# მომხმარებლებისა და უფლებების მართვის დიზაინი (Accounts and Permissions Design)

## Implementation Status

| ნაწილი | სტატუსი |
|--------|---------|
| Own profile GET/PUT `/api/accounts/ourself` | Implemented |
| Accounts list/detail/update/delete | Implemented (`can_users`) |
| Permission flags on profile (`can_users`, `can_recips`) | Implemented |
| Service accounts (`services` + `service_permissions`) | Implemented (`/api/services`, `/services` UI) |
| Permissions catalog REST list | Implemented (`can_permissions` or `can_users`) |
| Permissions catalog create/delete + `/permissions` UI | Implemented (`can_permissions` only) |
| Assign/revoke user permissions (`/api/accounts/<uuid>/permissions`) | Implemented |
| Register with optional permission codes | Implemented |
| Permission codes seeded | `can_users`, `can_permissions`, `can_recips`, `can_recips_read` |

აქტუალური endpoint-ები: [`09-api-inventory.md`](09-api-inventory.md).

---

## 1. დოკუმენტის მიზანი

დოკუმენტის მიზანია მომხმარებლების (Accounts) და უფლებების (Permissions) მართვის არქიტექტურის, მონაცემთა მოდელების, API Endpoint-ებისა და ავტორიზაციის მექანიზმების აღწერა.

სისტემა იყენებს **Permission-Based Authorization** მოდელს, სადაც უფლებები პირდაპირ ენიჭება მომხმარებლებს და არ გამოიყენება Roles (RBAC).

---

# 2. არქიტექტურული მიდგომა

```text
User
  │
  └── Permissions
```

ერთ მომხმარებელს შეიძლება ჰქონდეს რამდენიმე Permission, ხოლო ერთი Permission შეიძლება რამდენიმე მომხმარებელს ჰქონდეს.

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

# 3. მოდულის პასუხისმგებლობები

## Accounts

- საკუთარი პროფილის მიღება;
- საკუთარი პროფილის განახლება (`first_name`, `last_name`);
- მომხმარებლების სიის მიღება;
- მომხმარებლის დეტალური ინფორმაციის მიღება;
- მომხმარებლის რედაქტირება;
- მომხმარებლის აქტივაცია/დეაქტივაცია;
- მომხმარებლის წაშლა (როცა FK blockers იძლევა საშუალებას);
- საკუთარი ანგარიშის დეაქტივაცია/წაშლა აკრძალულია.

---

## Permissions

Implemented:

- Permission models (`permissions`, `user_permissions`);
- Runtime check via `user.check_permission(code)`;
- Seed via `flask populate_db`.

Planned (REST API ჯერ არ არის):

- უფლებების სიის მართვა;
- ახალი უფლებების შექმნა;
- არსებული უფლებების განახლება / soft deactivate;
- მომხმარებლისთვის უფლებების მინიჭება / გაუქმება API-ით.

---

# 4. მონაცემთა მოდელი

## users

| ველი | ტიპი | აღწერა |
|------|------|---------|
| id | bigint | პირველადი გასაღები |
| uuid | uuid | გარე იდენტიფიკატორი |
| email | varchar(255) | უნიკალური ელ-ფოსტა |
| first_name | varchar(100) | სახელი |
| last_name | varchar(100) | გვარი |
| is_active | boolean | მომხმარებლის აქტიური სტატუსი |
| created_by_user_id | bigint \| null | ვის მიერ შეიქმნა მომხმარებელი (`self-register` შემთხვევაში `null`) |
| created_at | datetime | შექმნის თარიღი |
| updated_at | datetime | განახლების თარიღი |
| updated_by_user_id | bigint | ვის მიერ განახლდა მისი მონაცემები ბოლოს |

---

## permissions

| ველი | ტიპი | აღწერა |
|------|------|---------|
| id | bigint | პირველადი გასაღები |
| code | varchar(100) | უნიკალური კოდი |
| name | varchar(255) | დასახელება |
| description | text | აღწერა |
| is_active | boolean | აქტიურია თუ არა permission |
| deactivated_at | datetime \| null | როდის გაუქმდა (soft deactivate) |
| deactivated_by_user_id | bigint \| null | ვის მიერ გაუქმდა |
| created_by_user_id | bigint | რომელი მომხმარებლის მიერ შეიქმნა |
| created_at | datetime | შექმნის თარიღი |
| updated_at | datetime | განახლების თარიღი |
| updated_by_user_id | bigint | რომელი მომხმარებლის მიერ განახლდა ბოლოს |

---

## user_permissions

| ველი | ტიპი | აღწერა |
|------|------|---------|
| id | bigint | პირველადი გასაღები |
| user_id | bigint | მომხმარებელი |
| permission_id | bigint | უფლება |
| granted_by_user_id | bigint | რომელი მომხმარებლის მიერ მიენიჭა |
| granted_at | datetime | როდის მიენიჭა |
| degranted_at | datetime \| null | როდის ჩამოერთვა (`null` = აქტიური) |
| degranted_by_user_id | bigint \| null | ვის მიერ ჩამოერთვა |

---

### DB Constraints და ინდექსები

- `users.uuid` -> `UNIQUE INDEX`;
- `users.email` -> `UNIQUE INDEX`;
- `permissions.code` -> `UNIQUE INDEX`;
- `permissions.is_active` -> ინდექსი აქტიური permission-ების სწრაფი ფილტრაციისთვის;
- `user_permissions.id` -> `PRIMARY KEY`;
- `users.created_by_user_id`, `users.updated_by_user_id` -> `FOREIGN KEY -> users.id`;
- `permissions.created_by_user_id`, `permissions.updated_by_user_id` -> `FOREIGN KEY -> users.id`;
- `permissions.deactivated_by_user_id` -> `FOREIGN KEY -> users.id`;
- `user_permissions.user_id` და `user_permissions.permission_id` -> ინდექსები სწრაფი join-ისთვის;
- `user_permissions.granted_by_user_id` -> `FOREIGN KEY -> users.id`;
- `user_permissions.degranted_by_user_id` -> `FOREIGN KEY -> users.id`;
- `user_permissions(user_id, permission_id, degranted_at)` -> ინდექსი აქტიური/ისტორიული ჩანაწერების სწრაფი მოძიებისთვის;
- ერთდროულად მხოლოდ ერთი აქტიური ჩანაწერია დასაშვები თითო `(user_id, permission_id)` წყვილზე (enforced service layer + transaction-ით);
- ყველა `FOREIGN KEY` უნდა იყოს `ON DELETE RESTRICT` (ისტორიის/მთლიანობის დასაცავად).

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

# 6. სტანდარტული უფლებები

| Code | სტატუსი | აღწერა |
|------|---------|---------|
| can_users | Seeded + used | რეგისტრაცია + accounts + services admin UI/API |
| can_permissions | Implemented | Permissions catalog CRUD + grant/revoke on accounts |
| can_recips | Seeded + used | Recipients write + Notify UI |
| can_recips_read | Seeded + used | Recipients read-only (service keys) |
| can_event_view | Implemented | მიწისძვრის მოვლენების ნახვა |
| can_event_edit | Implemented | მიწისძვრის მოვლენების შექმნა/რედაქტირება/წაშლა |


---

# 7. API Endpoint-ები

## საკუთარი მომხმარებლის მონაცემები

### საკუთარი პროფილის მიღება

```http
GET /api/accounts/ourself
```

Auth: JWT.

Response includes profile fields plus boolean flags:

- `can_users`
- `can_recips`

(გამოითვლება `check_permission`-ით, არა სრული permission list-ით.)

---

### საკუთარი პროფილის განახლება

```http
PUT /api/accounts/ourself
```

Auth: JWT. Body: `first_name`, `last_name`.

---

## მომხმარებლების მართვა

Required Permission ყველა admin endpoint-ზე:

```text
can_users
```

### მომხმარებლების სიის მიღება

```http
GET /api/accounts/
```

Response: `{ "items": [...], "total": N }`.

---

### მომხმარებლის დეტალური ინფორმაციის მიღება

```http
GET /api/accounts/{uuid}
```

---

### მომხმარებლის განახლება

```http
PUT /api/accounts/{uuid}
```

Fields: `first_name`, `last_name`, `email`, `is_active`.

წესი: მომხმარებელს არ შეუძლია საკუთარი ანგარიშის დეაქტივაცია.

---

### მომხმარებლის წაშლა

```http
DELETE /api/accounts/{uuid}
```

წესები:

- საკუთარი ანგარიშის წაშლა აკრძალულია;
- თუ FK blockers ხელს უშლის (RESTRICT), ბრუნდება conflict/error;
- წარმატებისას hard delete.

---

## უფლებების კატალოგი (Implemented)

აქტუალური REST ზედაპირი: [`09-api-inventory.md`](09-api-inventory.md#permissions-catalog--apipermissions).

- `GET/POST /api/permissions/` — სია / შექმნა (ან soft-deleted-ის re-activate)
- `GET/DELETE /api/permissions/<code_or_id>` — დეტალი / წაშლა (unassigned → hard; assigned → soft deactivate)
- მომხმარებელზე მინიჭება: `GET/POST/DELETE /api/accounts/<uuid>/permissions`
- რეგისტრაციაზე მინიჭება: `POST /api/auth/register` + optional `permission_codes`

- `GET /api/permissions/` — სია (`can_permissions` **ან** `can_users`, მინიჭებისთვის)
- `POST /api/permissions/` — შექმნა (`can_permissions` only)
- `DELETE /api/permissions/<code_or_id>` — წაშლა (`can_permissions` only)
- UI `/permissions` — მხოლოდ `can_permissions`
- მომხმარებელზე მინიჭება: `GET/POST/DELETE /api/accounts/<uuid>/permissions` (`can_users` ან `can_permissions`)

Required Permission (catalog create/delete / UI page): `can_permissions` only.

### უფლებების სიის მიღება

```http
GET /api/permissions/
```

---

### უფლების წაშლა / დეაქტივაცია

```http
DELETE /api/permissions/{code_or_id}
```

- თუ assignment არ აქვს → hard delete
- თუ user/service assignment აქვს → soft deactivate (`is_active=false`); ისტორია ინახება

---

### ახალი უფლების შექმნა

```http
POST /api/permissions/
```

Body: `code`, `name`, optional `description`.

---

### უფლების დეტალების მიღება

```http
GET /api/permissions/{code_or_id}
```

---

### უფლების განახლება

```http
PUT /api/permissions/{id}
```

Required Permission:

```text
can_permissions
```

---

## მომხმარებლის უფლებების მართვა (Implemented)

ნაწილი იმპლემენტირებულია accounts API-ზე. დეტალები: [`09-api-inventory.md`](09-api-inventory.md).

### მომხმარებლის უფლებების მიღება

```http
GET /api/accounts/{uuid}/permissions
```

Required Permission: `can_permissions`.

---

### მომხმარებლისთვის უფლებების მინიჭება

```http
POST /api/accounts/{uuid}/permissions
```

Required Permission: `can_permissions`.

Request:

```json
{
  "permission_codes": ["can_recips", "can_recips_read"]
}
```

ან `permission_ids` / `permissions`.

---

### მომხმარებლის უფლების გაუქმება

```http
DELETE /api/accounts/{uuid}/permissions/{permission_id}
```

Required Permission:

```text
can_permissions
```


---

### Permission Lifecycle (Grant / Revoke / Re-Grant)

აქტიური მინიჭება განისაზღვრება ასე:

```sql
degranted_at IS NULL
```

Grant:

- თუ `(user_id, permission_id)` წყვილზე აქტიური ჩანაწერი უკვე არსებობს -> `409 already_assigned`;
- სხვა შემთხვევაში იქმნება ახალი ჩანაწერი: `granted_at=NOW()`, `degranted_at=NULL`.

Revoke:

- მოიძებნება აქტიური ჩანაწერი და ახლდება: `degranted_at=NOW()`, `degranted_by_user_id=<actor_id>`;
- თუ აქტიური ჩანაწერი არ არსებობს -> `404 not_assigned` (ან idempotent `200`, API შეთანხმებით).

Re-Grant (მინიჭება ჩამორთმევის შემდეგ):

- ძველი ჩანაწერი არ იშლება და არ გადაიწერება;
- იქმნება ახალი ჩანაწერი ახალი `granted_at` დროით, რათა ისტორია სრულად შენარჩუნდეს.

Permission assignment უსაფრთხოების წესები:

- `can_permissions` მქონე მომხმარებელს შეუძლია ნებისმიერი permission-ის მინიჭება/გაუქმება ნებისმიერ მომხმარებელზე;
- `can_permissions` ითვლება პლატფორმის ადმინისტრაციულ უფლებად და მისი მინიჭება ხდება მხოლოდ სანდო ადმინისტრატორებზე;
- ოპერაცია სრულდება ტრანზაქციაში race condition-ების თავიდან ასაცილებლად.

---

## API Contract (საერთო წესები)

- Accounts list ამჟამად აბრუნებს `{ items, total }` (pagination query params — planned);
- ყველა შეცდომა ბრუნდება ერთიანი ფორმატით:

```json
{
  "error": "forbidden",
  "message": "Missing required permission: can_users"
}
```

- სტანდარტული authz error-ები: `forbidden`, `permission_denied`, `validation_error`, `conflict`, `not_found`, `already_assigned`, `not_assigned`.

---

# 8. ავტორიზაციის პროცესი

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

Permissions არ ინახება JWT Token-ში და ყოველი მოთხოვნის დროს იტვირთება მონაცემთა ბაზიდან ან Redis Cache-დან.

---

# 11. უსაფრთხოების მექანიზმები

- JWT Authentication;
- Permission-Based Authorization;
- HTTPS/SSL;
- Rate Limiting;
- Audit Logging;
- მომხმარებლის დეაქტივაცია (`is_active=false`);
- ცენტრალიზებული Permission Validation;
- `can_permissions`-ზე დაფუძნებული ცენტრალიზებული Permission Governance.

---

# 12. Audit Logging

სისტემა ინახავს:

- მომხმარებლის შექმნას;
- მომხმარებლის განახლებას;
- მომხმარებლის დეაქტივაციას;
- Permission-ის შექმნას;
- Permission-ის განახლებას;
- Permission-ის მინიჭებას;
- Permission-ის გაუქმებას;
- Permission-ის დეაქტივაციას.

თითოეული audit ჩანაწერი მინიმუმ შეიცავს:

- `event_type` (მაგ: `permission_assigned`);
- `actor_user_id` (ვინ შეასრულა);
- `target_user_id` ან `target_resource_id` (ვიზე/რაზე შესრულდა);
- `changes` (before/after snapshot ან diff);
- `ip_address`, `user_agent`;
- `request_id` (traceability-სთვის);
- `created_at`.

---

