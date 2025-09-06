import time, threading
from .base import BaseProvider, VideoJob

class MockProvider(BaseProvider):
    def __init__(self):
        self._jobs = {}

    def submit(self, prompt: str, options: dict) -> VideoJob:
        job_id = str(int(time.time() * 1000))
        job = VideoJob(job_id, status="processing")
        self._jobs[job_id] = job

        def _worker():
            time.sleep(2)  # simulate generation latency
            job.status = "succeeded"  # video served via /video/{job_id}

        threading.Thread(target=_worker, daemon=True).start()
        return job

    def fetch(self, job_id: str) -> VideoJob:
        return self._jobs.get(job_id) or VideoJob(job_id, status="not_found", error="Unknown job")
