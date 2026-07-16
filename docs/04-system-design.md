# სისტემის დეტალური დიზაინი (System Design Document)

## 1. დოკუმენტის მიზანი

დოკუმენტის მიზანია Earthquake Notification System (ENS)-ის შიდა ტექნიკური არქიტექტურის, მოდულების, მონაცემთა ნაკადების, სერვისების და კომპონენტებს შორის ურთიერთქმედების აღწერა.

---

# 2. არქიტექტურული მიდგომა

სისტემა აგებულია შემდეგი პრინციპებით:

- Modular Architecture
- Domain-Driven Design (DDD)
- Event-Driven Processing
- Asynchronous Processing
- Future Microservice Readiness

სისტემა არ წარმოადგენს კლასიკურ მონოლითურ აპლიკაციას და შედგება დამოუკიდებელი მოდულებისგან.

---

# 3. სისტემის ძირითადი მოდულები

```text
Identity Module
Earthquake Module
Notification Module
Administration Module
Monitoring Module
```

---

# 4. Identity Module

პასუხისმგებლობები:

- რეგისტრაცია;
- ავტორიზაცია;
- JWT Token-ების მართვა;
- პაროლის აღდგენა;
- მომხმარებლების მართვა;
- Permissions-ის მართვა;
- მოწყობილობების მართვა;
- Notification Preferences.

---

## ქვემოდულები

```text
authentication
accounts
permissions
devices
notification_preferences
```

---

# 5. Earthquake Module

პასუხისმგებლობები:

- SeisComP ინტეგრაცია;
- მოვლენების მიღება;
- მოვლენების დამუშავება;
- მოვლენების შენახვა.

---

## ქვემოდულები

```text
events
magnitudes
locations
shakemaps
```

---

# 6. Notification Module

პასუხისმგებლობები:

- Push შეტყობინებების გენერაცია;
- FCM ინტეგრაცია;
- APNs ინტეგრაცია;
- შეტყობინებების გაგზავნა;
- შეტყობინებების ისტორიის შენახვა.

---

## ქვემოდულები

```text
notifications
delivery
templates
subscriptions
```

---

# 7. Administration Module

პასუხისმგებლობები:

- სისტემური პარამეტრების მართვა;
- სტატისტიკის ნახვა;
- Audit Logs;
- ადმინისტრაციული ოპერაციები.

---

# 8. Monitoring Module

პასუხისმგებლობები:

- სისტემური მეტრიკები;
- ლოგირება;
- ალერტები;
- Dashboard-ები.

---

# 9. კომპონენტების ურთიერთქმედება

```text
Mobile Application
        │
        ▼
      Nginx
        │
        ▼
     REST API
        │
 ┌──────┼─────────┐
 │      │         │
 ▼      ▼         ▼
Identity Earthquake Notification
 Module    Module      Module
```

---

# 10. მონაცემთა ნაკადი

## მიწისძვრის მოვლენა

```text
SeisComP
     │
     ▼
Earthquake Service
     │
     ▼
MySQL Database
     │
     ▼
Notification Service
     │
     ▼
Mobile Applications
```

---

# 11. შეტყობინებების ნაკადი

```text
Earthquake Event
        │
        ▼
Notification Worker
        │
        ├── FCM
        └── APNs
                │
                ▼
          Mobile Devices
```

---

# 12. Authentication Flow

```text
User
  │
  ▼
Login Request
  │
  ▼
Authentication Module
  │
  ├── Validate Credentials
  ├── Generate JWT
  └── Generate Refresh Token
  │
  ▼
Response
```

---

# 13. Background Processing

სისტემა იყენებს ფონურ პროცესებს:

```text
worker-events
worker-notifications
scheduler
```

---

## worker-events

პასუხისმგებელია:

- SeisComP მოვლენების დამუშავებაზე;
- მონაცემთა სინქრონიზაციაზე.

---

## worker-notifications

პასუხისმგებელია:

- Push შეტყობინებების გაგზავნაზე;
- Retry მექანიზმზე.

---

## scheduler

პასუხისმგებელია:

- დაგეგმილ დავალებებზე;
- Cleanup Jobs;
- სინქრონიზაციის ამოცანებზე.

---

# 14. Docker არქიტექტურა

```text
nginx
api
mysql
redis
worker-events
worker-notifications
scheduler
prometheus
grafana
```

---

# 15. მონაცემთა ბაზის ძირითადი ობიექტები

```text
users
permissions
user_permissions

devices
notification_preferences

earthquakes
notifications
notification_logs

audit_logs
system_settings
```

---

# 16. უსაფრთხოების დიზაინი

სისტემა იყენებს:

- HTTPS/SSL;
- JWT Authentication;
- Permission-Based Authorization;
- Password Hashing (bcrypt);
- Rate Limiting;
- Audit Logging.

---

# 17. შეცდომების დამუშავება

სისტემა იყენებს:

- ცენტრალიზებულ Exception Handling-ს;
- Structured Logging-ს;
- Retry მექანიზმს;
- Dead Letter Queue-ს.

---

# 18. მონიტორინგი

გამოიყენება:

- Prometheus;
- Grafana;
- ELK Stack.

---

# 19. სარეზერვო მექანიზმები

- ავტომატური Backup;
- მონაცემთა აღდგენა;
- კონფიგურაციების Backup;
- ლოგების არქივაცია.

---

# 20. გაფართოების შესაძლებლობები

სისტემის არქიტექტურა მომავალში იძლევა შესაძლებლობას დამოუკიდებელ სერვისებად გამოიყოს:

```text
Identity Service
Earthquake Service
Notification Service
Analytics Service
Administration Service
```

მინიმალური ცვლილებებით და არსებული ბიზნეს-ლოგიკის შენარჩუნებით.