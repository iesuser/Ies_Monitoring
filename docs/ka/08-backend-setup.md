# Backend Setup (Flask-RESTx)

## 1. ვირტუალური გარემოს შექმნა

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux / macOS
source venv/bin/activate
```

---

## 2. დამოკიდებულებების დაყენება

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

დააყენე მინიმუმ `SECRET_KEY` / `JWT_SECRET_KEY` და (სურვილისამებრ) mail ცვლადები password reset-ისთვის.

---

## 4. ბაზის ინიციალიზაცია

```bash
flask --app run init_db --confirm-text RESET_DB
flask --app run populate_db
```

`populate_db` ქმნის/ააქტიურებს უფლებებს:

- `can_users`
- `can_permissions`
- `can_recips`
- `can_recips_read`

და admin მომხმარებელს (ყველა permission მინიჭებული):

- email: `roma.grigalashvili@iliauni.edu.ge`
- password: `PASSWORD` (შეცვალე პროდაქშენამდე)

---

## 5. აპლიკაციის გაშვება

```bash
python run.py
```

---

## 6. შემოწმება

| რესურსი | URL |
|---------|-----|
| App | `http://localhost:5000` |
| API Base | `http://localhost:5000/api` |
| Swagger UI | `http://localhost:5000/docs/` |
| Accounts UI | `http://localhost:5000/en/accounts` |
| Services UI | `http://localhost:5000/en/services` |
| Notify UI | `http://localhost:5000/en/notify` |
| Seismic Events UI | `http://localhost:5000/en/seismic_events` |
| Event details UI | `http://localhost:5000/en/seismic_events/<id>` |

> `GET /api/health` ჯერ არ არის იმპლემენტირებული (planned).

იმპლემენტირებული API-ების სრული სია: [`09-api-inventory.md`](09-api-inventory.md).  
Seismic Events: [`10-seismic-events.md`](10-seismic-events.md).

---

## 7. ტესტები

ტესტები იყენებს `TestingConfig`-ს (in-memory SQLite).

```bash
pytest
# ან
python -m pytest -v
```

ტესტების სტრუქტურა:

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

## 8. გარემოები

| `FLASK_ENV` | Config | DB default |
|-------------|--------|------------|
| `development` (default) | `DevelopmentConfig` | SQLite `dev.db` |
| `testing` | `TestingConfig` | in-memory SQLite |
| `production` | `ProductionConfig` | `PROD_DATABASE_URI` (MySQL recommended) |
