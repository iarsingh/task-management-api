from tasks.ops import router as ops_router
import hashlib
import hmac
import os
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, FastAPI, HTTPException, Query, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from tasks import db

SECRET = os.environ.get("TASK_SECRET", "dev-only-change-me-32-characters-min")
TOKEN_HOURS = int(os.environ.get("TASK_TOKEN_HOURS", "8"))
SALT = b"task-demo-salt"
app = FastAPI(title="Tasks")
app.include_router(ops_router, prefix="/v1")
bearer = HTTPBearer(auto_error=False)


def hash_password(password):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), SALT, 100_000).hex()


USERS = {"alice": hash_password("password"), "bob": hash_password("password")}


class Login(BaseModel):
    username: str
    password: str


class TaskIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class TaskPatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    done: bool | None = None


@contextmanager
def database():
    connection = db.connect(os.environ.get("TASK_DB", "tasks.db"))
    try:
        yield connection
    finally:
        connection.close()


def issue_token(username, hours=TOKEN_HOURS):
    expires = datetime.now(timezone.utc) + timedelta(hours=hours)
    return jwt.encode({"sub": username, "exp": expires}, SECRET, algorithm="HS256")


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


def clean_title(title):
    stripped = title.strip()
    if not stripped:
        raise HTTPException(status_code=422, detail="title is required")
    return stripped


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/token")
def token(body: Login):
    stored = USERS.get(body.username)
    if stored is None or not hmac.compare_digest(stored, hash_password(body.password)):
        raise HTTPException(status_code=401, detail="wrong username or password")
    return {"access_token": issue_token(body.username), "token_type": "bearer", "expires_in": TOKEN_HOURS * 3600}


@app.get("/tasks")
def get_tasks(
    owner: str = Depends(current_user),
    done: bool | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    with database() as connection:
        rows, total = db.list_tasks(connection, owner, done, limit, offset)
    return {"tasks": rows, "total": total, "limit": limit, "offset": offset}


@app.post("/tasks", status_code=201)
def post_task(body: TaskIn, owner: str = Depends(current_user)):
    with database() as connection:
        return db.add_task(connection, owner, clean_title(body.title))


@app.get("/tasks/{task_id}")
def get_task(task_id: int, owner: str = Depends(current_user)):
    with database() as connection:
        task = db.get_task(connection, owner, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")
    return task


@app.patch("/tasks/{task_id}")
def patch_task(task_id: int, body: TaskPatch, owner: str = Depends(current_user)):
    if body.title is None and body.done is None:
        raise HTTPException(status_code=422, detail="send title or done")
    title = None if body.title is None else clean_title(body.title)
    with database() as connection:
        task = db.update_task(connection, owner, task_id, title, body.done)
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")
    return task


@app.delete("/tasks/{task_id}", status_code=204)
def remove_task(task_id: int, owner: str = Depends(current_user)):
    with database() as connection:
        deleted = db.delete_task(connection, owner, task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="task not found")
    return Response(status_code=204)
