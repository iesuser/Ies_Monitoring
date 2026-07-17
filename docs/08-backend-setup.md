# Backend Setup (Flask-RESTx)

## 1. ვირტუალური გარემოს შექმნა

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 2. დამოკიდებულებების დაყენება

```bash
pip install -r requirements.txt
```

## 3. აპლიკაციის გაშვება

```bash
python run.py
```

## 4. შემოწმება

- API Base URL: `http://localhost:5000/api`
- Health Check: `GET /api/health`
- Swagger UI: `http://localhost:5000/api/docs`
