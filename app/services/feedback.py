# app/services/feedback.py:

import os
from datetime import datetime

FEEDBACK_FILE = os.path.join("app", "user_feedback.txt")

def save_feedback(job_id: str, prompt: str, liked: bool):
    """
    Append a feedback entry to app/user_feedback.txt
    Format: 2025-09-05 12:10 | job_id=abc123 | prompt="Make a cat video" | liked=True
    """
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    safe_prompt = prompt.replace("\n", " ").strip()
    line = f"{ts} | job_id={job_id} | prompt=\"{safe_prompt}\" | liked={liked}\n"

    # Ensure directory exists
    os.makedirs(os.path.dirname(FEEDBACK_FILE), exist_ok=True)

    with open(FEEDBACK_FILE, "a", encoding="utf-8") as f:
        f.write(line)

    return {"ok": True, "message": "Feedback saved"}
