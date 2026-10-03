import sqlite3


def connect(path):
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute(
        "CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY, owner TEXT NOT NULL, title TEXT NOT NULL, done INTEGER NOT NULL DEFAULT 0)"
    )
    return connection


def list_tasks(connection, owner):
    rows = connection.execute("SELECT id, owner, title, done FROM tasks WHERE owner = ? ORDER BY id", (owner,)).fetchall()
    return [dict(row) for row in rows]


def add_task(connection, owner, title):
    cursor = connection.execute("INSERT INTO tasks (owner, title) VALUES (?, ?)", (owner, title))
    connection.commit()
    return {"id": cursor.lastrowid, "owner": owner, "title": title, "done": 0}
