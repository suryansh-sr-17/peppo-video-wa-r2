from typing import Optional
from dataclasses import dataclass
import datetime
from app import requests_db

@dataclass
class RequestRecord:
    id: int
    user_id: str
    job_id: Optional[str]
    prompt: str
    status: str
    created_at: str

class RequestQueue:
    """Database-backed queue for handling multiple user requests."""

    def enqueue(self, user_id: str, prompt: str) -> int:
        """Add request to queue, return request ID."""
        return requests_db.insert_request(user_id, prompt)

    def dequeue(self) -> Optional[RequestRecord]:
        """Fetch next queued request (FIFO)."""
        row = requests_db.get_next_request()
        if not row:
            return None
        return RequestRecord(
            id=row["id"],
            user_id=row["user_id"],
            job_id=row["job_id"],
            prompt=row["prompt"],
            status=row["status"],
            created_at=row["created_at"],
        )

    def mark_processing(self, req_id: int, job_id: str):
        """Mark a request as processing with its assigned job_id."""
        requests_db.update_request_status(req_id, "processing", job_id)

    def mark_done(self, req_id: int, success: bool = True):
        """Mark request as completed (done or failed)."""
        status = "done" if success else "failed"
        requests_db.update_request_status(req_id, status)
