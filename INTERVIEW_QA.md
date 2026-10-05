# task-management-api — interview questions and answers

[README](README.md) · [Project architecture](PROJECT_ARCHITECTURE.md)

Answers below use this repository’s files and implementation. They distinguish existing behavior from suggested extensions; source links let you verify each walkthrough.

## 1. What problem does task-management-api address, and what can you demonstrate?

Alice and Bob sign in and keep separate task lists. Every query is scoped to the signed-in owner.

I would demonstrate the linked implementation or examples and distinguish that evidence from any planned production features. Start with [`README.md`](README.md).

## 2. How is this repository organized?

- [`src/tasks/main.py`](src/tasks/main.py): Implementation or supporting configuration.
- [`src/tasks/db.py`](src/tasks/db.py): Implementation or supporting configuration.
- [`requirements.txt`](requirements.txt): Implementation or supporting configuration.
- [`tests/test_tasks.py`](tests/test_tasks.py): Executable checks and regression examples.
- [`.github/workflows/ci.yml`](.github/workflows/ci.yml): GitHub Actions job definitions.
- [`README.md`](README.md): Project explanations or operating notes.

[PROJECT_ARCHITECTURE.md](PROJECT_ARCHITECTURE.md) contains the component diagram and the implementation walkthrough.

## 3. Can you walk through `current_user` and explain the decision it makes?

The main walkthrough here is `current_user(credentials: HTTPAuthorizationCredentials | None=Depends(bearer))` in [`src/tasks/main.py`](src/tasks/main.py#L56).

```python
def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
    if credentials is None:
        raise HTTPException(status_code=401, detail="missing bearer token")
    try:
        payload = jwt.decode(credentials.credentials, SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=401, detail="token expired") from exc
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="invalid token") from exc
    if payload.get("sub") not in USERS:
        raise HTTPException(status_code=401, detail="unknown user")
    return payload["sub"]
```

The implementation calls `Depends`, `HTTPException`, `jwt.decode`, `payload.get`. In an interview, trace those calls in execution order using a fixture input.

## 4. What responsibility does `connect` have?

`connect(path)` is defined in [`src/tasks/db.py`](src/tasks/db.py#L6).

Its return expressions include:

- `connection`

It uses `connection.execute`, `sqlite3.connect`. This is the code path I would compare against the caller to explain responsibility boundaries.

## 5. What input validation and failure behavior are implemented?

Explicit failure paths include:

- `HTTPException(status_code=401, detail='missing bearer token')` in [`src/tasks/main.py`](src/tasks/main.py#L58).
- `HTTPException(status_code=401, detail='unknown user')` in [`src/tasks/main.py`](src/tasks/main.py#L66).
- `HTTPException(status_code=422, detail='title is required')` in [`src/tasks/main.py`](src/tasks/main.py#L73).
- `HTTPException(status_code=401, detail='wrong username or password')` in [`src/tasks/main.py`](src/tasks/main.py#L86).
- `HTTPException(status_code=404, detail='task not found')` in [`src/tasks/main.py`](src/tasks/main.py#L113).
- `HTTPException(status_code=422, detail='send title or done')` in [`src/tasks/main.py`](src/tasks/main.py#L120).
- `HTTPException(status_code=404, detail='task not found')` in [`src/tasks/main.py`](src/tasks/main.py#L125).

I would test both the condition that reaches each exception and the caller that translates it. An explicit raise does not mean every malformed input or dependency failure is handled.

## 6. Which test would you use to demonstrate correctness?

[`tests/test_tasks.py`](tests/test_tasks.py#L23) contains `test_owner_sees_only_their_tasks`:

```python
def test_owner_sees_only_their_tasks():
    alice, bob = auth("alice"), auth("bob")
    created = client.post("/tasks", json={"title": "write the readout"}, headers=alice)
    assert created.status_code == 201
    assert created.json()["done"] is False
    assert client.get("/tasks", headers=bob).json()["tasks"] == []
    assert client.get("/tasks", headers=alice).json()["tasks"][0]["title"] == "write the readout"
```

This is a concrete regression example from the repository. Its assertions establish that case; they do not establish behavior for every input or under production load.

## 7. What HTTP interface does the code expose?

- `GET /healthz` → `healthz` in [`src/tasks/main.py`](src/tasks/main.py#L78).
- `POST /token` → `token` in [`src/tasks/main.py`](src/tasks/main.py#L83).
- `GET /tasks` → `get_tasks` in [`src/tasks/main.py`](src/tasks/main.py#L91).
- `POST /tasks` → `post_task` in [`src/tasks/main.py`](src/tasks/main.py#L103).
- `GET /tasks/{task_id}` → `get_task` in [`src/tasks/main.py`](src/tasks/main.py#L109).
- `PATCH /tasks/{task_id}` → `patch_task` in [`src/tasks/main.py`](src/tasks/main.py#L118).
- `DELETE /tasks/{task_id}` → `remove_task` in [`src/tasks/main.py`](src/tasks/main.py#L130).

These are literal decorators. Application/router prefixes, authentication, and middleware must be checked in the corresponding setup code.

## 8. Where does state live, and what happens with multiple workers?

Module-level containers include `USERS` in [`src/tasks/main.py`](src/tasks/main.py).

These containers belong to a Python process. Inspect which are constant fixtures and which are mutated. Mutable process state needs an explicit shared-storage or synchronization strategy before multiple workers can provide consistent behavior.

## 9. How would another engineer reproduce your walkthrough?

Start from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

These commands follow repository manifests; environment setup and command results still need to be checked on the target machine.

## 10. What does automation verify, and what does it not prove?

Inspect [`.github/workflows/ci.yml`](.github/workflows/ci.yml) for triggers, permissions, and job commands. I would name the checks that those definitions run and show the latest run separately. A workflow definition alone does not establish a successful deployment, security review, or production SLO.

## 11. How would you present this project in a Forward Deployed Engineer interview?

Start with the user and operational problem described in [`README.md`](README.md). Explain one constraint that changes the implementation, show the linked code or example, and walk through a success case and a failure case. Agree on a measurable acceptance criterion before expanding the solution, and leave a handoff with data boundaries and rollback ownership. Any proposed production or business metric should be identified as a target until measured.

## 12. What is the input-to-output contract of `current_user`?

In [`src/tasks/main.py`](src/tasks/main.py#L56), `current_user(credentials: HTTPAuthorizationCredentials | None=Depends(bearer))` receives the inputs. The function computes these intermediate values:

The implementation delegates or iterates directly; trace the calls in the source walkthrough.

Its result is defined by:

- `payload['sub']`

## 13. Which decision rules or boundary conditions should an interviewer challenge?

The implementation in [`src/tasks/main.py`](src/tasks/main.py#L56) branches on:

- `credentials is None`
- `payload.get('sub') not in USERS`

A useful extension is a table-driven test that covers each condition just below, at, and above its boundary where applicable. These expressions are the current rules; changing them changes behavior and should be justified by the project’s acceptance criteria.
