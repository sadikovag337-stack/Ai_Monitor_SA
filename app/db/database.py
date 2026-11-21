import sqlite3
from app.core.config import DB_PATH

def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with connect() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS cameras(
            id TEXT PRIMARY KEY, name TEXT NOT NULL, rtsp_url TEXT NOT NULL,
            vendor TEXT DEFAULT 'generic', enabled INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
