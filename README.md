# Earthquake Notification System (ENS)

Real-time earthquake notification platform for Android and iOS devices.

## Project Management

- Trello Board: [IES Monitoring](https://trello.com/b/ShiKsW69/iesmonitoring)

## Features

- Real-time earthquake event processing
- Push notifications for Android and iOS
- SeisComP integration
- User subscriptions and preferences
- Monitoring and analytics
- High availability and disaster recovery support

## Technology Stack

- Backend: Flask, Flask-RESTx
- Mobile: React Native
- Database: MySQL
- Queue & Cache: Redis, Celery
- Notifications: FCM, APNs
- Infrastructure: Docker, Nginx, Ubuntu
- Monitoring: Prometheus, Grafana, ELK

## Documentation

Documentation is available in English (`docs/en/`) and Georgian (`docs/ka/`). Both folders contain the same set of documents.

| Document | English | ქართული |
|----------|---------|---------|
| Project Overview | [en](docs/en/01-project-overview.md) | [ka](docs/ka/01-project-overview.md) |
| System Architecture | [en](docs/en/02-system-architecture.md) | [ka](docs/ka/02-system-architecture.md) |
| Software Requirements | [en](docs/en/03-software-requirements.md) | [ka](docs/ka/03-software-requirements.md) |
| System Design | [en](docs/en/04-system-design.md) | [ka](docs/ka/04-system-design.md) |
| Authentication Design | [en](docs/en/05-authentication-design.md) | [ka](docs/ka/05-authentication-design.md) |
| Accounts and Permissions Design | [en](docs/en/06-accounts-and-permissions-design.md) | [ka](docs/ka/06-accounts-and-permissions-design.md) |
| Notification Design | [en](docs/en/07-notification-design.md) | [ka](docs/ka/07-notification-design.md) |
| Backend Setup | [en](docs/en/08-backend-setup.md) | [ka](docs/ka/08-backend-setup.md) |
| API Inventory (Implemented) | [en](docs/en/09-api-inventory.md) | [ka](docs/ka/09-api-inventory.md) |
| Seismic Events (UI + API) | [en](docs/en/10-seismic-events.md) | [ka](docs/ka/10-seismic-events.md) |
| Alert Zones (API) | [en](docs/en/11-alert-zones.md) | [ka](docs/ka/11-alert-zones.md) |

## Current Backend Status

**Implemented**

- Auth: login, admin register, refresh/logout, password reset, change password
- Accounts admin UI/API (`/api/accounts/...`)
- Service accounts + API keys UI/API (`/api/services`, `/services`)
- Recipients UI/API (`/api/recips`, `/notify`)
- Alert zones API (`/api/alert_zones`): map polygons with ML magnitude range and notification target
- Permissions catalog REST (`/api/permissions`) + user grant/revoke on accounts
- Permissions seed + runtime checks (`can_users`, `can_permissions`, `can_recips`, `can_recips_read`, `can_event_view`, `can_event_edit`, `can_event_publish`)
- JWT + service `X-API-Key` auth
- Seismic Events API + Web UI: list/map/filters, create/edit, details page (incl. WordPress publish panel), magnitudes, beachball PNG generation
- WordPress publish/unpublish API + details UI (`/api/publish_events/publish|unpublish/<id>`)

**Planned**

- SeisComP automatic ingest / push delivery
- Redis/Celery workers
- Health endpoint

Source of truth for endpoints: [docs/en/09-api-inventory.md](docs/en/09-api-inventory.md).  
Seismic Events details: [docs/en/10-seismic-events.md](docs/en/10-seismic-events.md).

## Testing

```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest
```

API tests live in `tests/` and use an in-memory SQLite database via `TestingConfig`.
