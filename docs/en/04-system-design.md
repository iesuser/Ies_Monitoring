# System Design Document

## 1. Purpose

This document describes the internal technical architecture of the Earthquake Notification System (ENS): its modules, data flows, services and the interaction between components.

---

# 2. Architectural Approach

The system is built on the following principles:

- Modular Architecture
- Domain-Driven Design (DDD)
- Event-Driven Processing
- Asynchronous Processing
- Future Microservice Readiness

The system is not a classic monolithic application; it consists of independent modules.

---

# 3. Main Modules

```text
Identity Module
Earthquake Module
Notification Module
Administration Module
Monitoring Module
```

---

# 4. Identity Module

Responsibilities:

- Registration;
- Login;
- JWT token management;
- Password recovery;
- User management;
- Permission management;
- Device management;
- Notification Preferences.

---

## Submodules

```text
authentication          # implemented
accounts                # implemented
permissions             # models/seed implemented; REST planned
services / api_keys     # implemented
devices                 # planned
notification_preferences # planned
```

---

# 5. Earthquake Module

Responsibilities:

- SeisComP integration;
- Receiving events;
- Processing events;
- Storing events.

---

## Submodules

```text
events
magnitudes
locations
shakemaps
```

---

# 6. Notification Module

Responsibilities:

- Generating push notifications;
- FCM integration;
- APNs integration;
- Sending notifications;
- Storing notification history.

---

## Submodules

```text
recips              # implemented (email/phone contacts)
notifications       # planned
delivery            # planned
templates           # planned
subscriptions       # planned
```

---

# 7. Administration Module

Responsibilities:

- System settings management;
- Viewing statistics;
- Audit Logs;
- Administrative operations.

---

# 8. Monitoring Module

Responsibilities:

- System metrics;
- Logging;
- Alerts;
- Dashboards.

---

# 9. Component Interaction

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

# 10. Data Flow

## Earthquake event

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

# 11. Notification Flow

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

The system uses background processes:

```text
worker-events
worker-notifications
scheduler
```

---

## worker-events

Responsible for:

- Processing SeisComP events;
- Data synchronization.

---

## worker-notifications

Responsible for:

- Sending push notifications;
- Retry mechanism.

---

## scheduler

Responsible for:

- Scheduled tasks;
- Cleanup Jobs;
- Synchronization tasks.

---

# 14. Docker Architecture

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

# 15. Main Database Objects

```text
users
permissions
user_permissions
refresh_tokens

services
service_permissions

recips
recip_emails
recip_numbers

devices                  # planned
notification_preferences # planned

earthquakes              # planned (no model in app yet)
notifications            # planned
notification_logs        # planned

audit_logs               # planned
system_settings          # planned
```

---

# 16. Security Design

The system uses:

- HTTPS/SSL;
- JWT Authentication;
- Permission-Based Authorization;
- Password Hashing (Werkzeug);
- Rate Limiting;
- Audit Logging.

---

# 17. Error Handling

The system uses:

- Centralized exception handling;
- Structured logging;
- Retry mechanism;
- Dead Letter Queue.

---

# 18. Monitoring

Tools used:

- Prometheus;
- Grafana;
- ELK Stack.

---

# 19. Backup Mechanisms

- Automatic backups;
- Data recovery;
- Configuration backups;
- Log archiving.

---

# 20. Extensibility

The architecture allows the following to be split into independent services in the future:

```text
Identity Service
Earthquake Service
Notification Service
Analytics Service
Administration Service
```

with minimal changes and while preserving the existing business logic.
