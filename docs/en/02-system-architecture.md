# System Architecture

## 1. Overview

The Earthquake Notification System (ENS) is a real-time, scalable, highly available platform that provides:

- Receiving seismic data;
- Processing earthquake events;
- Sending notifications to users;
- Storing and analyzing data;
- System monitoring and administration.

The system follows the **Modular Architecture** principle and uses an **Event-Driven Processing** approach.

---

# 2. Architectural Principles

The system is based on the following principles:

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

# 3. High-Level Architecture

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

# 4. Architectural Style

The system uses:

## Modular Architecture

Business logic is split into independent modules.

## Event-Driven Processing

Services communicate with each other through events and queues.

## Asynchronous Processing

Long-running operations run in background processes (workers).

---

# 5. Main Services

## Identity Service

Responsible for:

- Registration;
- Login;
- User management;
- Permission management;
- Password recovery.

---

## Earthquake Service

Responsible for:

- SeisComP integration;
- Receiving earthquake events;
- Processing events;
- Storing events.

---

## Notification Service

Responsible for:

- Generating push notifications;
- FCM integration;
- APNs integration;
- Sending notifications.

---

## Monitoring Service

Responsible for:

- Metrics collection;
- Monitoring;
- Alert generation;
- Log management.

---

# 6. Modules

## Identity Module

```text
authentication          # implemented
accounts                # implemented
permissions             # models + checks implemented; REST planned
services / api_keys     # implemented
devices                 # planned
notification_preferences # planned
```

---

## Earthquake Module

```text
earthquakes             # planned
events
magnitudes
locations
shakemaps
```

---

## Notification Module

```text
recips                  # implemented (contacts admin)
notifications           # planned
templates               # planned
delivery                # planned
subscriptions           # planned
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

# 7. Data Flow

## Earthquake event processing

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

# 9. Infrastructure Components

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

# 10. Docker Architecture

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

# 11. Security Architecture

The system uses:

- HTTPS/SSL;
- JWT Authentication;
- Permission-Based Authorization;
- Firewall (UFW);
- Rate Limiting;
- Audit Logging.

---

# 12. Reliability and Continuity

The system provides:

- Automatic backups;
- Data replication;
- Fault tolerance;
- Asynchronous processing;
- System monitoring;
- Logging.

---

# 13. Scalability

The architecture allows the following to be split into independent services in the future:

- Identity Service;
- Earthquake Service;
- Notification Service;
- Analytics Service;
- Administration Service.

---

# 14. Architectural Decision

The system deliberately does not use a classic monolithic architecture.

The application follows a modular architecture, uses event-driven processing and asynchronous workers, which provides:

- Low coupling between components;
- High performance;
- Extensibility;
- Independent scaling;
- Fault isolation;
- Support for a future microservice architecture.
