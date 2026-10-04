import sqlite3

COLUMNS = "id, owner, title, done, created_at"


def connect(path):
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute(
        "CREATE TABLE IF NOT EXISTS tasks ("
        "id INTEGER PRIMARY KEY, owner TEXT NOT NULL, title TEXT NOT NULL, "
        "done INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
    )
    connection.execute("CREATE INDEX IF NOT EXISTS tasks_owner ON tasks (owner, id)")
    return connection


def to_dict(row):
    body = dict(row)
    body["done"] = bool(body["done"])
    return body


def list_tasks(connection, owner, done=None, limit=50, offset=0):
    query = f"SELECT {COLUMNS} FROM tasks WHERE owner = ?"
    params = [owner]
    if done is not None:
        query += " AND done = ?"
        params.append(int(done))
    total = connection.execute(query.replace(COLUMNS, "COUNT(*)"), params).fetchone()[0]
    rows = connection.execute(query + " ORDER BY id LIMIT ? OFFSET ?", [*params, limit, offset]).fetchall()
    return [to_dict(row) for row in rows], total


def get_task(connection, owner, task_id):
    row = connection.execute(f"SELECT {COLUMNS} FROM tasks WHERE id = ? AND owner = ?", (task_id, owner)).fetchone()
    return to_dict(row) if row else None


def add_task(connection, owner, title):
    cursor = connection.execute("INSERT INTO tasks (owner, title) VALUES (?, ?)", (owner, title))
    connection.commit()
    return get_task(connection, owner, cursor.lastrowid)


def update_task(connection, owner, task_id, title=None, done=None):
    if get_task(connection, owner, task_id) is None:
        return None
    if title is not None:
        connection.execute("UPDATE tasks SET title = ? WHERE id = ? AND owner = ?", (title, task_id, owner))
    if done is not None:
        connection.execute("UPDATE tasks SET done = ? WHERE id = ? AND owner = ?", (int(done), task_id, owner))
    connection.commit()
    return get_task(connection, owner, task_id)


def delete_task(connection, owner, task_id):
    cursor = connection.execute("DELETE FROM tasks WHERE id = ? AND owner = ?", (task_id, owner))
    connection.commit()
    return cursor.rowcount == 1
