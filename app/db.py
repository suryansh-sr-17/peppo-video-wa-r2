# app/db.py
import sqlite3
import os

DB_PATH = os.getenv("DB_PATH", "jobs.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        job_id TEXT UNIQUE,
        prompt TEXT,
        final_prompt TEXT,
        status TEXT,
        video_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        style TEXT
    )
    """)
    conn.commit()
    conn.close()

# ---------------- NEW FUNCTIONS ----------------

def insert_job(user_id: str, rec):
    """Insert a new job into the DB (ignore if already exists)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT OR IGNORE INTO jobs (user_id, job_id, prompt, final_prompt, status, video_url, created_at, style)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        rec.job_id,
        rec.prompt,
        rec.final_prompt,
        rec.status,
        rec.video_path,
        rec.created_at,
        rec.chosen_style or rec.style,   # support both fields
    ))
    conn.commit()
    conn.close()

def update_job_status(job_id: str, status: str, video_url: str = None):
    """Update status (and video URL if present) for a job."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE jobs
        SET status = ?, video_url = ?
        WHERE job_id = ?
    """, (status, video_url, job_id))
    conn.commit()
    conn.close()

def get_jobs_for_user(user_id: str, limit: int = 10):
    """Fetch recent jobs for a given user_id, newest first."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT job_id, prompt, final_prompt, status, video_url, created_at, style
        FROM jobs
        WHERE user_id = ?
        ORDER BY datetime(created_at) DESC
        LIMIT ?
    """, (user_id, limit))
    rows = cur.fetchall()
    conn.close()
    return rows

