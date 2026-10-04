# Task management REST API

Level: Beginner+

Skills: FastAPI, PostgreSQL-shaped SQL, CRUD, JWT, Pytest

Alice and Bob sign in and keep separate task lists. Every query is scoped to the signed-in owner.

The default database is a local SQLite file using the same table shape you would point at PostgreSQL. Set the path with `TASK_DB`. The signing secret is `TASK_SECRET`; tokens last `TASK_TOKEN_HOURS`, 8 by default.

Demo passwords are the literal `password` for `alice` and `bob`. They are stored as PBKDF2 hashes and compared in constant time. Replace the users and the salt before any shared deployment.

```bash
pip install -r requirements.txt
pytest -q
PYTHONPATH=src uvicorn tasks.main:app --reload
```

## Endpoints

| Method and path | Does |
| --- | --- |
| `POST /token` | Username and password in, bearer token out |
| `GET /tasks?done=true&limit=50&offset=0` | Your tasks, with a total for paging |
| `POST /tasks` | Create. Title 1 to 200 characters, not blank. Returns 201 |
| `GET /tasks/{id}` | One task |
| `PATCH /tasks/{id}` | Change `title`, `done`, or both. An empty body is refused |
| `DELETE /tasks/{id}` | Delete. Returns 204 |

```bash
TOKEN=$(curl -s -X POST localhost:8000/token -H 'content-type: application/json' \
  -d '{"username":"alice","password":"password"}' | python -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')
curl -s -X POST localhost:8000/tasks -H "Authorization: Bearer $TOKEN" -H 'content-type: application/json' -d '{"title":"write the readout"}'
```

## Rules the tests hold

- A missing, malformed, or expired token is 401. An expired token says so.
- Another user's task is 404, not 403, so ids do not reveal what exists.
- Bob cannot read, change, or delete Alice's task.
