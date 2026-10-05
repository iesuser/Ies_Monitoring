# Backend Setup (Flask-RESTx)

## 1. Create a virtual environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux / macOS
source venv/bin/activate
```

---

## 2. Install dependencies

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

---

## 3. Environment

```bash
copy .env.example .env   # Windows
# cp .env.example .env   # Linux / macOS
```

Set at least `SECRET_KEY` / `JWT_SECRET_KEY` and (optionally) the mail variables for password reset.

---

## 4. Initialize the database

```bash
flask --app run init_db --confirm-text RESET_DB
flask --app run populate_db
```

`populate_db` creates/activates the permissions:

- `can_users`
- `can_permissions`
- `can_recips`
- `can_recips_read`

and an admin user (with all permissions granted):

- email: `roma.grigalashvili@iliauni.edu.ge`
- password: `PASSWORD` (change before production)

---

## 5. Run the application

```bash
python run.py
```

---

## 6. Check

| Resource | URL |
|----------|-----|
| App | `http://localhost:5000` |
| API Base | `http://localhost:5000/api` |
| Swagger UI | `http://localhost:5000/docs/` |
| Accounts UI | `http://localhost:5000/en/accounts` |
| Services UI | `http://localhost:5000/en/services` |
| Notify UI | `http://localhost:5000/en/notify` |
| Seismic Events UI | `http://localhost:5000/en/seismic_events` |
| Event details UI | `http://localhost:5000/en/seismic_events/<id>` |

> `GET /api/health` is not implemented yet (planned).

Full list of implemented APIs: [`09-api-inventory.md`](09-api-inventory.md).  
Seismic Events: [`10-seismic-events.md`](10-seismic-events.md).

---

## 7. Tests

Tests use `TestingConfig` (in-memory SQLite).

```bash
pytest
# or
python -m pytest -v
```

Test structure:

```text
tests/
  conftest.py
  helpers.py
  test_auth_api.py
  test_accounts_api.py
  test_services_api.py
  test_recips_api.py
  test_permissions_api.py
  test_seismic_events_api.py
```

---

## 8. Environments

| `FLASK_ENV` | Config | DB default |
|-------------|--------|------------|
| `development` (default) | `DevelopmentConfig` | SQLite `dev.db` |
| `testing` | `TestingConfig` | in-memory SQLite |
| `production` | `ProductionConfig` | `PROD_DATABASE_URI` (MySQL recommended) |
