# შეტყობინებების დიზაინი (Notification Design)

## 1. დოკუმენტის მიზანი

დოკუმენტის მიზანია მიწისძვრებისა და სისტემური შეტყობინებების მიმღებთა (Recipients) მართვის არქიტექტურისა და მონაცემთა მოდელების აღწერა.

### Implementation Status

| ნაწილი | სტატუსი |
|--------|---------|
| Recipients (`recips` + emails + numbers) | Implemented |
| Admin UI `/notify` | Implemented |
| Permission `can_recips` (write) | Implemented |
| Permission `can_recips_read` (list/detail) | Implemented |
| Service API keys for read-only access | Implemented (see Services API) |
| Alert zones (`/api/alert_zones`) | Implemented (API), see [`11-alert-zones.md`](11-alert-zones.md) |
| Push / Devices / Queue / History / Templates | Planned |

---

## 2. არქიტექტურული მიდგომა

Notification Recipients დამოუკიდებელია Identity Users-ისგან.

მიმღები არის კონტაქტის ერთეული (`recip`), რომელსაც შეიძლება ჰქონდეს რამდენიმე email და რამდენიმე ტელეფონის ნომერი.

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

## 3. მოდულის პასუხისმგებლობები (implemented)

- Recipient-ების შექმნა / განახლება / წაშლა;
- Email არხების დამატება / განახლება / წაშლა;
- Phone არხების დამატება / განახლება / წაშლა;
- Staff / External გამიჯვნა (`is_staff`);
- Soft disable არხზე ან მთელ recipient-ზე (`is_active`).

---

## 4. მონაცემთა მოდელი

## recips

| ველი | ტიპი | აღწერა |
|------|------|---------|
| id | int | პირველადი გასაღები |
| username | varchar(255) | მიმღების სახელი / აღწერა |
| is_staff | boolean | თანამშრომელია თუ გარე კონტაქტი |
| is_active | boolean | აქტიური სტატუსი |
| created_at | datetime | შექმნის თარიღი |
| updated_at | datetime | განახლების თარიღი |
| created_by_user_id | int \| null | ვინ შექმნა |
| updated_by_user_id | int \| null | ვინ განაახლა |

---

## recip_emails

| ველი | ტიპი | აღწერა |
|------|------|---------|
| id | int | პირველადი გასაღები |
| recip_id | int | FK → recips.id |
| email | varchar(255) | უნიკალური ელ-ფოსტა |
| is_active | boolean | აქტიური სტატუსი |
| created_at / updated_at | datetime | აუდიტი |
| created_by_user_id / updated_by_user_id | int \| null | აუდიტი |

---

## recip_numbers

| ველი | ტიპი | აღწერა |
|------|------|---------|
| id | int | პირველადი გასაღები |
| recip_id | int | FK → recips.id |
| phone_number | varchar(50) | უნიკალური ნომერი, ფორმატი `+9955XXXXXXXX` |
| is_active | boolean | აქტიური სტატუსი |
| created_at / updated_at | datetime | აუდიტი |
| created_by_user_id / updated_by_user_id | int \| null | აუდიტი |

Constraints:

- `recip_emails.email` → UNIQUE
- `recip_numbers.phone_number` → UNIQUE
- emails/numbers cascade-ით იშლება recipient-თან ერთად

---

## 5. API Endpoint-ები

### Read (list / detail)

Required permission (any of):

```text
can_recips
can_recips_read
```

Auth: JWT Bearer **ან** service `X-API-Key`.

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

Create body მაგალითი:

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

- გვერდი: `/<lang>/notify`
- Navbar-ში ჩანს მხოლოდ `can_recips` უფლების მქონე მომხმარებლისთვის
- CRUD + email/phone მართვა modal-ებით

---

## 7. უსაფრთხოება

- JWT Authentication **ან** service API key (`X-API-Key`);
- Read: `can_recips` ან `can_recips_read`;
- Write: `can_recips`;
- Email normalize/validate;
- Georgian phone normalize (`+9955XXXXXXXX`);
- Soft disable (`is_active=false`);
- Audit user ids recipient/channel ჩანაწერებზე.

---

## 8. მომავალი გაფართოებები (Planned)

შემდეგ ეტაპზე Notification Module გაფართოვდება:

- Push Notifications (FCM / APNs);
- Device Management;
- Notification History;
- Notification Templates;
- Notification Queue & Retry Mechanism;
- მიწისძვრის მოვლენებთან ავტომატური მიწოდების ინტეგრაცია.
