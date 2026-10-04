import pytest
from fastapi.testclient import TestClient

from tasks.main import app, issue_token

client = TestClient(app)


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    monkeypatch.setenv("TASK_DB", str(tmp_path / "tasks.db"))


def auth(username):
    response = client.post("/token", json={"username": username, "password": "password"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def create(headers, title):
    return client.post("/tasks", json={"title": title}, headers=headers).json()


def test_owner_sees_only_their_tasks():
    alice, bob = auth("alice"), auth("bob")
    created = client.post("/tasks", json={"title": "write the readout"}, headers=alice)
    assert created.status_code == 201
    assert created.json()["done"] is False
    assert client.get("/tasks", headers=bob).json()["tasks"] == []
    assert client.get("/tasks", headers=alice).json()["tasks"][0]["title"] == "write the readout"


def test_missing_and_bad_tokens_are_401():
    assert client.get("/tasks").status_code == 401
    assert client.get("/tasks", headers={"Authorization": "Bearer nope"}).status_code == 401


def test_expired_token_is_401():
    expired = issue_token("alice", hours=-1)
    response = client.get("/tasks", headers={"Authorization": f"Bearer {expired}"})
    assert response.status_code == 401
    assert response.json()["detail"] == "token expired"


def test_wrong_password_is_401():
    assert client.post("/token", json={"username": "alice", "password": "guess"}).status_code == 401


def test_another_users_task_is_404_not_403():
    alice, bob = auth("alice"), auth("bob")
    task = create(alice, "private")
    assert client.get(f"/tasks/{task['id']}", headers=bob).status_code == 404
    assert client.patch(f"/tasks/{task['id']}", json={"done": True}, headers=bob).status_code == 404
    assert client.delete(f"/tasks/{task['id']}", headers=bob).status_code == 404
    assert client.get(f"/tasks/{task['id']}", headers=alice).json()["done"] is False


def test_patch_marks_done_and_renames():
    alice = auth("alice")
    task = create(alice, "draft")
    updated = client.patch(f"/tasks/{task['id']}", json={"title": "final", "done": True}, headers=alice).json()
    assert updated["title"] == "final"
    assert updated["done"] is True


def test_empty_patch_is_refused():
    alice = auth("alice")
    task = create(alice, "draft")
    assert client.patch(f"/tasks/{task['id']}", json={}, headers=alice).status_code == 422


def test_delete_then_get_is_404():
    alice = auth("alice")
    task = create(alice, "temporary")
    assert client.delete(f"/tasks/{task['id']}", headers=alice).status_code == 204
    assert client.get(f"/tasks/{task['id']}", headers=alice).status_code == 404


def test_filter_by_done_and_paginate():
    alice = auth("alice")
    ids = [create(alice, f"task {n}")["id"] for n in range(5)]
    client.patch(f"/tasks/{ids[0]}", json={"done": True}, headers=alice)
    done = client.get("/tasks", params={"done": True}, headers=alice).json()
    assert [task["id"] for task in done["tasks"]] == [ids[0]]
    page = client.get("/tasks", params={"limit": 2, "offset": 2}, headers=alice).json()
    assert page["total"] == 5
    assert [task["title"] for task in page["tasks"]] == ["task 2", "task 3"]


def test_blank_and_long_titles_are_refused():
    alice = auth("alice")
    assert client.post("/tasks", json={"title": "   "}, headers=alice).status_code == 422
    assert client.post("/tasks", json={"title": "x" * 201}, headers=alice).status_code == 422
