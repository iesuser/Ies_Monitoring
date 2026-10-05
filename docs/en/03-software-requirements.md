# Software Requirements Specification

## 1. Purpose

This document defines the functional and non-functional requirements of the Earthquake Notification System (ENS).

It is the main basis for the development, testing, deployment and ongoing support of the system.

---

# 2. System Goals

The system aims to:

- Receive seismic events in real time;
- Process earthquake data;
- Notify users in a timely manner;
- Deliver push notifications to Android and iOS devices;
- Store and administer data securely.

---

# 3. User Types

## Unregistered user

Capabilities:

- Registration;
- Login.

---

## Registered user

Capabilities:

- Signing in;
- Viewing earthquakes;
- Managing their own profile;
- Changing notification preferences;
- Receiving push notifications.

---

## Administrator

Capabilities:

- User management;
- Permission management;
- Viewing statistics;
- Sending system notifications;
- System administration.

---

# 4. Functional Requirements

## FR-01 User registration

The system must support registering new users.

---

## FR-02 Login

The system must support user login with email and password.

---

## FR-03 Session management

The system must provide:

- JWT Access Token;
- Refresh Token;
- Logout.

---

## FR-04 Password recovery

The system must support password recovery via email.

---

## FR-05 User profile

Users must be able to:

- View their own profile;
- Update their own data.

---

## FR-06 User management

Administrators must be able to:

- Get the list of users;
- Edit user data;
- Activate and deactivate users.

---

## FR-07 Permission management

Administrators must be able to:

- Get the list of permissions;
- Create a new permission;
- Update an existing permission;
- Delete a permission;
- Grant permissions to a user;
- Revoke permissions.

---

## FR-08 Device management

The system must support:

- Device registration;
- Push token updates;
- Device deactivation.

---

## FR-09 Earthquake event processing

The system must support:

- Receiving data from SeisComP;
- Processing data;
- Storing data.

---

## FR-10 Earthquake history

Users must be able to:

- View the list of earthquakes;
- View detailed information.

**Implementation note (admin Web UI):** `/<lang>/seismic_events` (list, map, server-side filter) and `/<lang>/seismic_events/<id>` (summary, publish panel, Overview / Magnitudes / Beachball / Map). Details: [`10-seismic-events.md`](10-seismic-events.md). SeisComP auto-ingest and the mobile client are planned.

---

## FR-11 Push notifications

The system must support:

- Sending notifications to Android devices;
- Sending notifications to iOS devices.

---

## FR-12 Notification preferences

Users must be able to:

- Set a minimum magnitude;
- Turn notifications on/off;
- Select regions.

---

## FR-13 System notifications

Administrators must be able to:

- Send informational notifications;
- Send technical notifications.

---

## FR-14 Statistics and monitoring

The system must provide:

- System metrics;
- User statistics;
- Notification statistics.

---

# 5. Non-Functional Requirements

## NFR-01 Availability

System availability must be at least:

```text
99.9%
```

---

## NFR-02 Performance

Average API response time:

```text
≤ 300 ms
```

---

## NFR-03 Push notification delivery time

Maximum time from receiving an earthquake event to sending the notification:

```text
≤ 10 seconds
```

---

## NFR-04 Security

The system must use:

- HTTPS/SSL;
- JWT Authentication;
- Password Hashing;
- Rate Limiting;
- Audit Logging.

---

## NFR-05 Scalability

The system must support:

- Horizontal scaling;
- Adding more workers;
- Integrating additional services.

---

## NFR-06 Data protection

The system must provide:

- Automatic backups;
- Data recovery;
- Data integrity protection.

---

## NFR-07 Monitoring

The system must provide:

- Metrics Collection;
- Alerting;
- Centralized Logging.

---

# 6. Constraints

- Backend platform: Python
- Mobile platform: React Native
- Database: MySQL
- Queue system: Redis
- Infrastructure: Docker
- Operating system: Ubuntu Linux

---

# 7. External Integrations

## SeisComP

Source of seismic events.

---

## Firebase Cloud Messaging (FCM)

Android push notifications.

---

## Apple Push Notification Service (APNs)

iOS push notifications.

---

## SMTP Service

Sending email.

---

# 8. Acceptance Criteria

The system is considered successfully deployed if:

- Users can register and log in;
- Earthquake data is processed automatically;
- Push notifications are delivered successfully;
- The system runs securely and stably;
- Monitoring and logging are in place;
- Data backups and recovery are available.
