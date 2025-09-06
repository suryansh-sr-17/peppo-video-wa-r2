import sqlite3

DB_PATH = "jobs.db"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Add style column if not exists
try:
    cur.execute("ALTER TABLE jobs ADD COLUMN style TEXT;")
    print("✅ Added 'style' column")
except sqlite3.OperationalError as e:
    print(f"Skipped 'style': {e}")

# Add final_prompt column if not exists
try:
    cur.execute("ALTER TABLE jobs ADD COLUMN final_prompt TEXT;")
    print("✅ Added 'final_prompt' column")
except sqlite3.OperationalError as e:
    print(f"Skipped 'final_prompt': {e}")

conn.commit()
conn.close()
