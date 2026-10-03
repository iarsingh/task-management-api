import os

from fastapi.testclient import TestClient

os.environ["TASK_DB"] = "/tmp/ladder-tasks.db"
from tasks.main import app

client = TestClient(app)


def auth(username):
    token = client.post("/token", json={"username": username, "password": "password"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_owner_sees_only_their_tasks():
    alice = auth("alice")
    bob = auth("bob")
    created = client.post("/tasks", json={"title": "write the readout"}, headers=alice)
    assert created.status_code == 200
    assert client.get("/tasks", headers=bob).json()["tasks"] == []
    assert client.get("/tasks", headers=alice).json()["tasks"][0]["title"] == "write the readout"
    assert client.get("/tasks").status_code == 401
