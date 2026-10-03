# Task management REST API

Level: Beginner+

Skills: FastAPI, PostgreSQL-shaped SQL, CRUD, JWT, Pytest

Alice and Bob sign in and keep separate task lists. A missing token is rejected.

The default database is a local SQLite file using the same table shape you would point at PostgreSQL with `TASK_DB`. Passwords in this demo are the literal `password` for `alice` and `bob`. Replace that before any shared deployment. The signing secret is `TASK_SECRET`.

```bash
pip install -r requirements.txt
pytest -q
PYTHONPATH=src uvicorn tasks.main:app --reload
```

