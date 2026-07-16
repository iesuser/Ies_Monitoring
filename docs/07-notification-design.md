# შეტყობინებების დიზაინი (Notification Design)

## 1. დოკუმენტის მიზანი

დოკუმენტის მიზანია მიწისძვრებისა და სისტემური შეტყობინებების მიმღებთა (Recipients) მართვის არქიტექტურისა და მონაცემთა მოდელების აღწერა.

მოდული უზრუნველყოფს:

- SMS მიმღებების მართვას;
- Email მიმღებების მართვას;
- შეტყობინებების მიმღებთა ადმინისტრირებას;
- თანამშრომლებისა და გარე მიმღებების გამიჯვნას;
- შეტყობინებების არხების (Channels) მომავალი გაფართოების შესაძლებლობას.

---

# 2. არქიტექტურული მიდგომა

Notification მოდული დამოუკიდებელია Identity Module-ისგან.

SMS და Email მიმღებები არ არიან სისტემის მომხმარებლები და არ გადიან ავტორიზაციას.

```text
Users
    │
    └── Identity Service

SMS Contacts
Email Contacts
    │
    └── Notification Service
```

---

# 3. მოდულის პასუხისმგებლობები

## SMS Contacts

- SMS მიმღებების დამატება;
- SMS მიმღებების განახლება;
- SMS მიმღებების გააქტიურება/დეაქტივაცია;
- თანამშრომლების და გარე კონტაქტების მართვა.

---

## Email Contacts

- Email მიმღებების დამატება;
- Email მიმღებების განახლება;
- Email მიმღებების გააქტიურება/დეაქტივაცია;
- თანამშრომლების და გარე კონტაქტების მართვა.

---

# 4. მონაცემთა მოდელი

## sms_contacts

| ველი | ტიპი | აღწერა |
|------|------|---------|
| id | bigint | პირველადი გასაღები |
| name | varchar(255) | მიმღების სახელი |
| phone_number | varchar(50) | ტელეფონის ნომერი |
| description | varchar(500) | დამატებითი აღწერა |
| is_staff | boolean | თანამშრომლის სტატუსი |
| is_active | boolean | აქტიური სტატუსი |
| created_at | datetime | შექმნის თარიღი |
| updated_at | datetime | განახლების თარიღი |

---

## email_contacts

| ველი | ტიპი | აღწერა |
|------|------|---------|
| id | bigint | პირველადი გასაღები |
| name | varchar(255) | მიმღების სახელი |
| email | varchar(255) | ელ-ფოსტა |
| description | varchar(500) | დამატებითი აღწერა |
| is_staff | boolean | თანამშრომლის სტატუსი |
| is_active | boolean | აქტიური სტატუსი |
| created_at | datetime | შექმნის თარიღი |
| updated_at | datetime | განახლების თარიღი |

---

# 5. DB Constraints

## sms_contacts

- `phone_number` -> `UNIQUE INDEX`
- `is_staff` -> `DEFAULT FALSE`
- `is_active` -> `DEFAULT TRUE`

---

## email_contacts

- `email` -> `UNIQUE INDEX`
- `is_staff` -> `DEFAULT FALSE`
- `is_active` -> `DEFAULT TRUE`

---

# 6. Entity Relationship

ამ ეტაპზე კონტაქტები არ არის დაკავშირებული `users` ცხრილთან.

```text
sms_contacts

email_contacts
```

ორივე დამოუკიდებლად ფუნქციონირებს.

---

# 7. API Endpoint-ები

## SMS Contacts

### SMS კონტაქტების სიის მიღება

```http
GET /api/sms_contacts
```

Required Permission:

```text
can_notifications
```

---

### SMS კონტაქტის დამატება

```http
POST /api/sms_contacts
```

Required Permission:

```text
can_notifications
```

---

### SMS კონტაქტის განახლება

```http
PUT /api/sms_contacts/{id}
```

Required Permission:

```text
can_notifications
```

---

### SMS კონტაქტის წაშლა

```http
DELETE /api/sms_contacts/{id}
```

Required Permission:

```text
can_notifications
```

---

## Email Contacts

### Email კონტაქტების სიის მიღება

```http
GET /api/email_contacts
```

Required Permission:

```text
can_notifications
```

---

### Email კონტაქტის დამატება

```http
POST /api/email_contacts
```

Required Permission:

```text
can_notifications
```

---

### Email კონტაქტის განახლება

```http
PUT /api/email_contacts/{id}
```

Required Permission:

```text
can_notifications
```

---

### Email კონტაქტის წაშლა

```http
DELETE /api/email_contacts/{id}
```

Required Permission:

```text
can_notifications
```

---

# 8. გამოყენების მაგალითები

## SMS Contact

```text
Name: NSMC Duty Officer
Phone Number: +995599123456
Description: მორიგე სეისმოლოგი
Is Staff: true
```

---

## Email Contact

```text
Name: Emergency Service
Email: emergency@example.ge
Description: საგანგებო სიტუაციების მართვის სამსახური
Is Staff: false
```

---

# 9. უსაფრთხოების მექანიზმები

- JWT Authentication;
- Permission-Based Authorization;
- Audit Logging;
- Rate Limiting;
- Soft Disable (`is_active=false`).

---

# 10. Audit Logging

სისტემა ინახავს:

- კონტაქტის შექმნას;
- კონტაქტის განახლებას;
- კონტაქტის წაშლას;
- კონტაქტის გააქტიურებას;
- კონტაქტის დეაქტივაციას.

---

# 11. არქიტექტურული გადაწყვეტილება

Notification Recipients ინახება დამოუკიდებელ ცხრილებში და არ არის დაკავშირებული მომხმარებლების (Users) სისტემასთან.

ეს მიდგომა უზრუნველყოფს:

- მარტივ ადმინისტრირებას;
- გარე ორგანიზაციების მხარდაჭერას;
- ავტორიზაციის სისტემისგან დამოუკიდებლობას;
- Notification Module-ის დამოუკიდებელ განვითარებას.

---

# 12. მომავალი გაფართოებები

შემდეგ ეტაპზე Notification Module გაფართოვდება:

- Push Notifications;
- Device Management;
- Notification History;
- Notification Templates;
- Notification Queue & Retry Mechanism.