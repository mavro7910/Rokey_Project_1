# db/db.py
import sqlite3, hashlib
from pathlib import Path

# 1) 단일 경로로 통일 (프로젝트 루트의 app.db)
DB_PATH = Path("app.db").resolve()

def get_db_path() -> str:
    return str(DB_PATH)

def _connect():
    return sqlite3.connect(str(DB_PATH))

def ensure_schema():
    conn = _connect()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_path TEXT NOT NULL,
            label TEXT,
            confidence REAL,
            description TEXT,
            image_hash TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )
    """)
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_notes_image_path ON notes(image_path)")
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_notes_image_hash ON notes(image_hash)")
    conn.commit()
    conn.close()

def _file_sha256(fpath: str) -> str:
    h = hashlib.sha256()
    with open(fpath, "rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def insert_note(image_path: str, description: str, label: str=None, confidence: float=None) -> bool:
    """
    성공 시 True, UNIQUE로 무시되면 False.
    테이블이 없다면 ensure_schema() 후 1회 재시도.
    """
    ihash = _file_sha256(image_path)
    conn = _connect()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT OR IGNORE INTO notes (image_path, label, confidence, description, image_hash) VALUES (?, ?, ?, ?, ?)",
            (image_path, label, confidence, description, ihash)
        )
        conn.commit()
    except sqlite3.OperationalError as e:
        # no such table: notes → 자동 스키마 생성 후 1회 재시도
        if "no such table" in str(e):
            conn.close()
            ensure_schema()
            conn = _connect()
            cur = conn.cursor()
            cur.execute(
                "INSERT OR IGNORE INTO notes (image_path, label, confidence, description, image_hash) VALUES (?, ?, ?, ?, ?)",
                (image_path, label, confidence, description, ihash)
            )
            conn.commit()
        else:
            conn.close()
            raise
    ok = (cur.rowcount == 1)
    conn.close()
    return ok

def fetch_notes(limit: int = 200):
    ensure_schema()
    conn = _connect()
    rows = conn.execute(
        "SELECT id, image_path, label, confidence, description, created_at "
        "FROM notes ORDER BY datetime(created_at) DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return rows

def search_notes(label=None, keyword=None, date_from=None, date_to=None, limit: int = 200):
    ensure_schema()
    conn = _connect()
    base = "SELECT id, image_path, label, confidence, description, created_at FROM notes WHERE 1=1"
    args = []
    if label:
        base += " AND label = ?"; args.append(label)
    if keyword:
        w = f"%{keyword}%"
        base += " AND (image_path LIKE ? OR label LIKE ? OR description LIKE ?)"
        args.extend([w, w, w])
    if date_from:
        base += " AND date(created_at) >= date(?)"; args.append(date_from)
    if date_to:
        base += " AND date(created_at) <= date(?)"; args.append(date_to)
    base += " ORDER BY datetime(created_at) DESC LIMIT ?"; args.append(limit)
    rows = conn.execute(base, args).fetchall()
    conn.close()
    return rows

def delete_notes(ids):
    if not ids: return 0
    ensure_schema()
    conn = _connect()
    q = "DELETE FROM notes WHERE id IN ({})".format(",".join(["?"]*len(ids)))
    cur = conn.cursor()
    cur.execute(q, ids)
    conn.commit()
    n = cur.rowcount
    conn.close()
    return n
