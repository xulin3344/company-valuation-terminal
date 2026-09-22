"""SQLite 项目存取：保存/载入/列出/删除估值项目。

表结构：projects(id, name, ticker, market, created_at, updated_at, payload)
payload 为完整假设包 JSON。
"""
import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
import sys

if getattr(sys, "frozen", False):
    # 打包为 exe 时，将用户项目数据持久化在当前 exe 所在目录下的 data 目录中，避免打包在临时释放目录
    DEFAULT_DB_PATH = Path(sys.executable).resolve().parent / "data" / "projects.db"
else:
    DEFAULT_DB_PATH = Path(__file__).resolve().parents[2] / "data" / "projects.db"


def _connect(db_path: Path = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path else DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            ticker TEXT NOT NULL,
            market TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            payload TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


def save_project(
    name: str,
    ticker: str,
    market: str,
    payload: dict,
    project_id: Optional[str] = None,
    db_path: Path = None,
) -> dict:
    conn = _connect(db_path)
    now = datetime.now().isoformat()
    pid = project_id or str(uuid.uuid4())
    existing = conn.execute("SELECT id FROM projects WHERE id = ?", (pid,)).fetchone()
    if existing:
        conn.execute(
            "UPDATE projects SET name=?, ticker=?, market=?, updated_at=?, payload=? WHERE id=?",
            (name, ticker, market, now, json.dumps(payload, ensure_ascii=False), pid),
        )
    else:
        conn.execute(
            "INSERT INTO projects (id, name, ticker, market, created_at, updated_at, payload) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (pid, name, ticker, market, now, now, json.dumps(payload, ensure_ascii=False)),
        )
    conn.commit()
    row = conn.execute("SELECT * FROM projects WHERE id = ?", (pid,)).fetchone()
    conn.close()
    return _row_to_dict(row)


def load_project(project_id: str, db_path: Path = None) -> Optional[dict]:
    conn = _connect(db_path)
    row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    conn.close()
    return _row_to_dict(row) if row else None


def list_projects(db_path: Path = None) -> list:
    conn = _connect(db_path)
    rows = conn.execute("SELECT * FROM projects ORDER BY updated_at DESC").fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def delete_project(project_id: str, db_path: Path = None) -> bool:
    conn = _connect(db_path)
    cur = conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    conn.commit()
    deleted = cur.rowcount > 0
    conn.close()
    return deleted


def _row_to_dict(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "ticker": row["ticker"],
        "market": row["market"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "payload": json.loads(row["payload"]),
    }


__all__ = ["save_project", "load_project", "list_projects", "delete_project", "DEFAULT_DB_PATH"]