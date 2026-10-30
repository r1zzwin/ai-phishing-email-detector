import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone

CATEGORIES = ("Low", "Medium", "High", "Critical")

SCHEMA = """
CREATE TABLE IF NOT EXISTS scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    sender TEXT NOT NULL,
    subject TEXT NOT NULL,
    score INTEGER NOT NULL,
    category TEXT NOT NULL,
    ai_verdict TEXT,
    report_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_scans_created ON scans (created_at DESC);
"""


def _connect(db_path):
    conn = sqlite3.connect(db_path, timeout=5)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path):
    with closing(_connect(db_path)) as conn:
        conn.executescript(SCHEMA)
        conn.commit()


def save_scan(db_path, email, result):
    """Save one scan. The email body is deliberately NOT stored."""
    report = {
        "rule_findings": result["rules"]["findings"],
        "rule_points": result["score"]["rule_points"],
        "ai": result["ai"],
        "ai_error": result["ai_error"],
        "explanation": result["score"]["explanation"],
    }
    ai_verdict = result["ai"]["verdict"] if result["ai"] else None
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    with closing(_connect(db_path)) as conn:
        cursor = conn.execute(
            "INSERT INTO scans "
            "(created_at, sender, subject, score, category, ai_verdict, report_json) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                created_at,
                email["sender"],
                email["subject"],
                result["score"]["score"],
                result["score"]["category"],
                ai_verdict,
                json.dumps(report),
            ),
        )
        conn.commit()
        return cursor.lastrowid


def list_scans(db_path, search="", category=""):
    sql = "SELECT id, created_at, sender, subject, score, category FROM scans"
    where, params = [], []

    if search:
        escaped = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        where.append("(sender LIKE ? ESCAPE '\\' OR subject LIKE ? ESCAPE '\\')")
        params += [f"%{escaped}%", f"%{escaped}%"]
    if category in CATEGORIES:
        where.append("category = ?")
        params.append(category)

    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY created_at DESC, id DESC LIMIT 200"

    with closing(_connect(db_path)) as conn:
        return [dict(row) for row in conn.execute(sql, params).fetchall()]


def get_scan(db_path, scan_id):
    with closing(_connect(db_path)) as conn:
        row = conn.execute("SELECT * FROM scans WHERE id = ?", (scan_id,)).fetchone()
    if row is None:
        return None
    scan = dict(row)
    scan["report"] = json.loads(scan.pop("report_json"))
    return scan


def delete_scan(db_path, scan_id):
    with closing(_connect(db_path)) as conn:
        cursor = conn.execute("DELETE FROM scans WHERE id = ?", (scan_id,))
        conn.commit()
        return cursor.rowcount


def clear_scans(db_path):
    with closing(_connect(db_path)) as conn:
        conn.execute("DELETE FROM scans")
        conn.commit()