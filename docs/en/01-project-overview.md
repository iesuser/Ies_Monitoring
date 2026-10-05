# Earthquake Notification System (ENS)

## 1. Project Overview

The Earthquake Notification System (ENS) is a real-time earthquake notification platform whose goal is to process seismic events automatically and deliver instant notifications to Android and iOS users.

The system is integrated with the SeisComP seismic processing infrastructure and handles receiving, processing, storing and distributing earthquake events.

---

## Implementation Status (Backend)

| Module | Status |
|--------|--------|
| Identity: Auth (login/register/refresh/logout/reset) | Implemented |
| Identity: Accounts admin UI/API | Implemented |
| Service accounts + API keys + Services UI | Implemented |
| Permissions models + seed + runtime checks | Implemented |
| Permissions catalog REST (list/create/delete) | Implemented |
| Notification recipients (`recips`) + `/notify` UI | Implemented |
| Seismic Events API + list/filter/details UI + beachball images | Implemented |
| Push / Devices / Queue / Earthquake ingest | Planned |

Detailed API list: [`09-api-inventory.md`](09-api-inventory.md).  
Seismic Events UI/API details: [`10-seismic-events.md`](10-seismic-events.md).

---

# 2. Project Goals

The main goals of the project are:

- Timely notification of the public about earthquakes;
- Near real-time distribution of earthquake data;
- Centralized management of seismic data;
- Personalized notifications based on user preferences;
- A reliable, secure and scalable infrastructure.

---

# 3. Core Functionality

## For users

- Registration and login;
- Viewing the list of earthquakes;
- Viewing detailed earthquake information;
- Receiving push notifications;
- Managing notification preferences;
- Support for multiple devices.

---

## For administrators

- User management;
- User permission management;
- Sending system notifications;
- Viewing statistics and monitoring data;
- System administration.

---

# 4. Main System Components

## Mobile Applications

- Android Application
- iOS Application

---

## Identity Service

Responsible for:

- Registration;
- Login;
- Session management;
- Password recovery;
- User management;
- Permission management.

---

## Earthquake Service

Responsible for:

- Receiving data from SeisComP;
- Processing earthquake events;
- Storing and distributing events.

---

## Notification Service

Responsible for:

- Generating push notifications;
- Sending notifications to Android and iOS devices;
- Managing notification queues.

---

## Database Layer

Provides:

- Storage of user data;
- Storage of earthquake events;
- Notification history;
- System configuration.

---

## Monitoring and Logging

Provides:

- System monitoring;
- Metrics collection;
- Centralized log management;
- Alerts when problems are detected.

---

# 5. Main System Requirements

## Functional requirements

- User registration and login;
- Processing earthquake events;
- Sending push notifications;
- Managing user preferences;
- Administrative functions;
- Monitoring and logging.

---

## Non-functional requirements

- High Availability;
- Scalability;
- Security;
- Fault Tolerance;
- Data backups;
- High Performance.

---

# 6. Technologies

| Category | Technology |
|----------|------------|
| Backend | Python, Flask, Flask-RESTx |
| Mobile | React Native |
| Database | MySQL |
| Cache & Queue | Redis |
| Background Processing | Celery |
| Push Notifications | Firebase Cloud Messaging (FCM), Apple Push Notification Service (APNs) |
| Web Server | Nginx |
| Infrastructure | Ubuntu Linux |
| Containerization | Docker, Docker Compose |
| Monitoring | Prometheus, Grafana |
| Logging | ELK Stack |
| Security | HTTPS/SSL, JWT |

---

# 7. Architectural Principles

The system is built on the following principles:

- Modular Architecture;
- Domain-Driven Design (DDD);
- Event-Driven Processing;
- Loose Coupling;
- High Cohesion;
- Asynchronous Processing;
- Future Microservice Readiness.

---

# 8. Target Users

- The general public;
- Government agencies;
- Emergency management services;
- Scientific and research organizations;
- Seismologists and researchers.

---

# 9. Key Advantages

- Real-time notifications;
- High reliability;
- Cross-platform support;
- Modern and scalable architecture;
- Secure data management;
- Easy extensibility;
- Support for integrating new services.

---

# 10. Intended Outcome

The ultimate goal of the project is to build a modern, reliable and scalable earthquake notification platform in Georgia that ensures fast distribution of seismic events and timely notification of users.
