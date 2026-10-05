# Task management REST API

<!-- project-guide:start -->
## Project guide

[Project architecture](PROJECT_ARCHITECTURE.md) · [Interview questions and answers](INTERVIEW_QA.md)

Use the architecture document for the component diagram, implementation boundaries, and verification entry points. The interview guide includes source-backed answers and project walkthroughs.

### Implementation map

| Component | Responsibility |
| --- | --- |
| [`src/tasks/main.py`](src/tasks/main.py) | HTTP handlers: `GET /healthz`, `POST /token`, `GET /tasks`, `POST /tasks`, `GET /tasks/{task_id}` |
| [`src/tasks/db.py`](src/tasks/db.py) | Functions: `connect`, `to_dict`, `list_tasks`, `get_task`, `add_task`, `update_task`, `delete_task` |
| [`requirements.txt`](requirements.txt) | Implementation or supporting configuration |
| [`tests/test_tasks.py`](tests/test_tasks.py) | Executable checks and regression examples |
| [`.github/workflows/ci.yml`](.github/workflows/ci.yml) | GitHub Actions job definitions |
| [`README.md`](README.md) | Project explanations or operating notes |

### Local setup and verification

From the repository root (the commands follow the checked-in manifests):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

To serve the FastAPI application locally, install the server separately if it is not already available:

```bash
python -m pip install uvicorn
PYTHONPATH=src python -m uvicorn tasks.main:app --reload
```

<!-- project-guide:end -->

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

## Ops plane

Workspaces, tenant isolation, job approval, and audit live under `/v1`. Production apply is refused. See `docs/ARCHITECTURE.md`.
