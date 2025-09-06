# app/services/jobs.py:

from typing import Dict, Optional, List
from dataclasses import dataclass, field
import datetime
from app import db  # <-- import db so we can persist

@dataclass
class JobRecord:
    job_id: str
    status: str
    video_path: Optional[str]
    provider: str
    prompt_hash: str

    # NEW fields
    prompt: Optional[str] = None
    final_prompt: Optional[str] = None
    created_at: Optional[str] = None

    cached: bool = False
    meta: Dict[str, str] = field(default_factory=dict)

    # Feedback fields
    feedback_pending: bool = False
    feedback: Optional[bool] = None  # True=👍, False=👎, None=not given yet

    # New fields for style selection flow
    awaiting_style: bool = False
    chosen_style: Optional[str] = None
    style: Optional[str] = None


class JobStore:
    def __init__(self):
        self._by_id: Dict[str, JobRecord] = {}
        self._by_hash: Dict[str, JobRecord] = {}
        self._by_user: Dict[str, List[str]] = {}

    def get_by_hash(self, h: str) -> Optional[JobRecord]:
        return self._by_hash.get(h)

    def put(self, rec: JobRecord, user_id: str = None):
        self._by_id[rec.job_id] = rec
        if rec.prompt_hash:
            self._by_hash[rec.prompt_hash] = rec
        if user_id:
            if not rec.created_at:
                rec.created_at = datetime.datetime.utcnow().isoformat() + "Z"
            db.insert_job(user_id, rec)

    def get(self, job_id: str) -> Optional[JobRecord]:
        return self._by_id.get(job_id)

    def store_user_job(self, user_number: str, job_id: str):
        if not user_number:
            return
        lst = self._by_user.setdefault(user_number, [])
        if not lst or lst[-1] != job_id:
            lst.append(job_id)

    def get_jobs_for_user(self, user_number: str) -> List[str]:
        return list(self._by_user.get(user_number, []))

    def get_last_job_for_user(self, user_number: str) -> Optional[JobRecord]:
        jobs = self._by_user.get(user_number)
        if not jobs:
            return None
        return self.get(jobs[-1])

    def get_history_for_user(self, user_number: str, limit: int = 10) -> List[JobRecord]:
        recs: List[JobRecord] = []
        job_ids = self._by_user.get(user_number, [])
        for jid in job_ids:
            r = self.get(jid)
            if r:
                recs.append(r)

        try:
            rows = db.get_jobs_for_user(user_number, limit)
            for row in rows:
                recs.append(JobRecord(
                    job_id=row["job_id"],
                    status=row["status"],
                    video_path=row["video_url"],
                    provider="sqlite",
                    prompt_hash="",
                    prompt=row["prompt"],
                    final_prompt=row["final_prompt"],
                    created_at=row["created_at"],
                    style=row["style"],   # ✅ add this
                ))
        except Exception:
            pass

        try:
            recs.sort(key=lambda r: r.created_at or "", reverse=True)
        except Exception:
            pass

        return recs[:limit]

    def update_status_in_db(self, job_id: str, status: str, video_url: str = None):
        try:
            db.update_job_status(job_id, status, video_url)
        except Exception:
            pass

    # --- Feedback helpers ---
    def mark_feedback_pending(self, job_id: str):
        rec = self.get(job_id)
        if rec:
            rec.feedback_pending = True

    def mark_feedback_received(self, job_id: str, liked: bool):
        rec = self.get(job_id)
        if rec:
            rec.feedback_pending = False
            rec.feedback = liked

    def set_pending_prompt(self, user_number: str, prompt: str):
        # store a temporary record before style is chosen
        rec = JobRecord(
            job_id=f"pending-{user_number}",
            status="pending",
            video_path=None,
            provider="pending",
            prompt_hash="",
            prompt=prompt,
            created_at=datetime.datetime.utcnow().isoformat() + "Z",
            awaiting_style=True
        )
        self._by_id[rec.job_id] = rec
        self._by_user[user_number] = [rec.job_id]
        return rec

    def get_pending_prompt(self, user_number: str) -> Optional[JobRecord]:
        jobs = self._by_user.get(user_number)
        if not jobs:
            return None
        rec = self.get(jobs[-1])
        if rec and rec.awaiting_style:
            return rec
        return None
