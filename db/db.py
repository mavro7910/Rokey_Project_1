# db/db.py
import sqlite3
from datetime import datetime
from utils.config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS image_notes(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  image_path TEXT NOT NULL,
  description TEXT NOT NULL,
  created_at TEXT NOT NULL
);
"""

def _ensure_columns(conn):
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(image_notes)")
    cols = {row[1] for row in cur.fetchall()}  # column name set
    if "label" not in cols:
        conn.execute("ALTER TABLE image_notes ADD COLUMN label TEXT;")
    if "confidence" not in cols:
        conn.execute("ALTER TABLE image_notes ADD COLUMN confidence REAL;")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.execute(SCHEMA)
    _ensure_columns(conn)
    return conn

def insert_note(image_path: str, description: str, label: str = None, confidence: float = None):
    conn = get_conn()
    with conn:
        conn.execute(
            "INSERT INTO image_notes(image_path, description, created_at, label, confidence) "
            "VALUES (?, ?, ?, ?, ?)",
            (image_path, description, datetime.now().isoformat(timespec="seconds"), label, confidence)
        )
    conn.close()

def fetch_notes(limit: int = 200, keyword: str | None = None):
    conn = get_conn()
    cur = conn.cursor()
    base = "SELECT id, image_path, COALESCE(label,''), COALESCE(confidence,''), description, created_at FROM image_notes"
    if keyword:
        cur.execute(base + " WHERE description LIKE ? ORDER BY id DESC LIMIT ?", (f"%{keyword}%", limit))
    else:
        cur.execute(base + " ORDER BY id DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows
