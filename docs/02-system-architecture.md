# სისტემის არქიტექტურა (System Architecture)

## 1. მიმოხილვა

Earthquake Notification System (ENS) წარმოადგენს რეალურ დროში მოქმედ, მასშტაბირებად და მაღალი ხელმისაწვდომობის მქონე პლატფორმას, რომელიც უზრუნველყოფს:

- სეისმური მონაცემების მიღებას;
- მიწისძვრის მოვლენების დამუშავებას;
- მომხმარებლებისთვის შეტყობინებების გაგზავნას;
- მონაცემების შენახვასა და ანალიზს;
- სისტემის მონიტორინგსა და ადმინისტრირებას.

სისტემა აგებულია **Modular Architecture** პრინციპით და იყენებს **Event-Driven Processing** მიდგომას.

---

# 2. არქიტექტურული პრინციპები

სისტემა ეფუძნება შემდეგ პრინციპებს:

- Separation of Concerns (SoC)
- Domain-Driven Design (DDD)
- Loose Coupling
- High Cohesion
- Event-Driven Architecture
- Asynchronous Processing
- Scalability
- High Availability
- Fault Tolerance
- Future Microservice Readiness

---

# 3. მაღალი დონის არქიტექტურა

```text
                   ┌──────────────────┐
                   │     SeisComP     │
                   └────────┬─────────┘
                            │
                            ▼
                 ┌────────────────────┐
                 │ Earthquake Service │
                 └─────────┬──────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │    Redis    │
                    │    Queue    │
                    └──────┬──────┘
                           │
           ┌───────────────┼────────────────┐
           │               │                │
           ▼               ▼                ▼
┌────────────────┐ ┌──────────────┐ ┌──────────────┐
│ Notification   │ │ Analytics    │ │ Archive      │
│ Worker         │ │ Worker       │ │ Worker       │
└────────┬───────┘ └──────┬───────┘ └──────┬───────┘
         │                │                │
         └────────────────┼────────────────┘
                          │
                          ▼
                  ┌──────────────┐
                  │  MySQL DB    │
                  └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐
                  │  REST API    │
                  └──────┬───────┘
                         │
          ┌──────────────┼──────────────┐
          │                             │
          ▼                             ▼
 ┌─────────────────┐           ┌─────────────────┐
 │ Android Client  │           │   iOS Client    │
 └─────────────────┘           └─────────────────┘
```

---

# 4. არქიტექტურული სტილი

სისტემა იყენებს:

## Modular Architecture

ბიზნეს-ლოგიკა დაყოფილია დამოუკიდებელ მოდულებად.

## Event-Driven Processing

სერვისები ერთმანეთთან ურთიერთობენ მოვლენებისა და რიგების (Queues) გამოყენებით.

## Asynchronous Processing

დროით ხანგრძლივი ოპერაციები სრულდება ფონურ პროცესებში (Workers).

---

# 5. ძირითადი სერვისები

## Identity Service

პასუხისმგებელია:

- რეგისტრაციაზე;
- ავტორიზაციაზე;
- მომხმარებლების მართვაზე;
- Permissions-ის მართვაზე;
- პაროლის აღდგენაზე.

---

## Earthquake Service

პასუხისმგებელია:

- SeisComP ინტეგრაციაზე;
- მიწისძვრის მოვლენების მიღებაზე;
- მოვლენების დამუშავებაზე;
- მოვლენების შენახვაზე.

---

## Notification Service

პასუხისმგებელია:

- Push შეტყობინებების გენერაციაზე;
- FCM ინტეგრაციაზე;
- APNs ინტეგრაციაზე;
- შეტყობინებების გაგზავნაზე.

---

## Monitoring Service

პასუხისმგებელია:

- მეტრიკების შეგროვებაზე;
- მონიტორინგზე;
- ალერტების გენერაციაზე;
- ლოგების მართვაზე.

---

# 6. მოდულები

## Identity Module

```text
authentication
accounts
permissions
devices
notification_preferences
```

---

## Earthquake Module

```text
earthquakes
events
magnitudes
locations
shakemaps
```

---

## Notification Module

```text
notifications
templates
delivery
subscriptions
```

---

## Administration Module

```text
dashboard
statistics
system_settings
audit_logs
```

---

# 7. მონაცემთა ნაკადი (Data Flow)

## მიწისძვრის მოვლენის დამუშავება

```text
SeisComP
     │
     ▼
Earthquake Service
     │
     ▼
Database
     │
     ▼
Notification Service
     │
     ▼
Mobile Applications
```

---

# 8. Push Notification Flow

```text
Earthquake Event
        │
        ▼
Notification Service
        │
        ├── Android (FCM)
        └── iOS (APNs)
                │
                ▼
        Mobile Devices
```

---

# 9. ინფრასტრუქტურული კომპონენტები

## Application Layer

- REST API
- Background Workers
- Scheduler

## Data Layer

- MySQL
- Redis

## Infrastructure Layer

- Ubuntu Linux
- Docker
- Docker Compose
- Nginx

## Monitoring Layer

- Prometheus
- Grafana
- ELK Stack

---

# 10. Docker არქიტექტურა

```text
api
mysql
redis
worker-events
worker-notifications
scheduler
nginx
prometheus
grafana
```

---

# 11. უსაფრთხოების არქიტექტურა

სისტემა იყენებს:

- HTTPS/SSL;
- JWT Authentication;
- Permission-Based Authorization;
- Firewall (UFW);
- Rate Limiting;
- Audit Logging.

---

# 12. საიმედოობა და უწყვეტობა

სისტემა უზრუნველყოფს:

- ავტომატურ სარეზერვო ასლებს;
- მონაცემთა რეპლიკაციას;
- შეცდომების მიმართ მდგრადობას;
- ასინქრონულ დამუშავებას;
- სისტემის მონიტორინგს;
- ლოგირებას.

---

# 13. მასშტაბირებადობა

სისტემის არქიტექტურა იძლევა შესაძლებლობას მომავალში დამოუკიდებელ სერვისებად გამოიყოს:

- Identity Service;
- Earthquake Service;
- Notification Service;
- Analytics Service;
- Administration Service.

---

# 14. არქიტექტურული გადაწყვეტილება

სისტემა შეგნებულად არ იყენებს კლასიკურ მონოლითურ არქიტექტურას.

აპლიკაცია აგებულია მოდულური არქიტექტურის პრინციპით, იყენებს მოვლენებზე დაფუძნებულ დამუშავებას (Event-Driven Processing) და ასინქრონულ სამუშაო პროცესებს (Workers), რაც უზრუნველყოფს:

- კომპონენტების დაბალ დამოკიდებულებას;
- მაღალი წარმადობას;
- სისტემის გაფართოების შესაძლებლობას;
- დამოუკიდებელ მასშტაბირებას;
- შეცდომების იზოლაციას;
- მომავალი მიკროსერვისული არქიტექტურის მხარდაჭერას.