import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from tasks.db import add_task, connect, list_tasks

SECRET = os.environ.get("TASK_SECRET", "dev-only-change-me-32-characters-min")
USERS = {"alice": "password", "bob": "password"}
app = FastAPI(title="Tasks")
bearer = HTTPBearer()
DB_PATH = os.environ.get("TASK_DB", "tasks.db")


class Login(BaseModel):
    username: str
    password: str


class TaskIn(BaseModel):
    title: str


def current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="invalid token") from exc
    return payload["sub"]


@app.post("/token")
def token(body: Login):
    if USERS.get(body.username) != body.password:
        raise HTTPException(status_code=401, detail="unknown user")
    expires = datetime.now(timezone.utc) + timedelta(hours=8)
    encoded = jwt.encode({"sub": body.username, "exp": expires}, SECRET, algorithm="HS256")
    return {"access_token": encoded, "token_type": "bearer"}


@app.get("/tasks")
def get_tasks(owner: str = Depends(current_user)):
    connection = connect(DB_PATH)
    try:
        return {"tasks": list_tasks(connection, owner)}
    finally:
        connection.close()


@app.post("/tasks")
def post_task(body: TaskIn, owner: str = Depends(current_user)):
    if not body.title.strip():
        raise HTTPException(status_code=422, detail="title is required")
    connection = connect(DB_PATH)
    try:
        return add_task(connection, owner, body.title.strip())
    finally:
        connection.close()
