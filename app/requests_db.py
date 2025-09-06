import sqlite3
import os

# Separate database file just for queued requests
REQ_DB_PATH = os.getenv("REQ_DB_PATH", "requests.db")

def get_connection():
    conn = sqlite3.connect(REQ_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the requests queue table."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        job_id TEXT,
        prompt TEXT,
        status TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

# ---------------- Queue operations ----------------

def insert_request(user_id: str, prompt: str) -> int:
    """Add a new request to the queue with status=queued."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO requests (user_id, prompt, status)
        VALUES (?, ?, 'queued')
    """, (user_id, prompt))
    conn.commit()
    req_id = cur.lastrowid
    conn.close()
    return req_id

def get_next_request():
    """Fetch the oldest queued request (FIFO)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM requests
        WHERE status = 'queued'
        ORDER BY created_at ASC
        LIMIT 1
    """)
    row = cur.fetchone()
    conn.close()
    return row

def update_request_status(req_id: int, status: str, job_id: str = None):
    """Update the request status (and attach job_id if provided)."""
    conn = get_connection()
    cur = conn.cursor()
    if job_id:
        cur.execute(
            "UPDATE requests SET status = ?, job_id = ? WHERE id = ?",
            (status, job_id, req_id),
        )
    else:
        cur.execute(
            "UPDATE requests SET status = ? WHERE id = ?",
            (status, req_id),
        )
    conn.commit()
    conn.close()
