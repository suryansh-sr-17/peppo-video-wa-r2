from abc import ABC, abstractmethod
from typing import Optional, Dict

class VideoJob:
    def __init__(self, job_id: str, status: str = "queued",
                 video_url: Optional[str] = None, error: Optional[str] = None):
        self.job_id = job_id
        self.status = status
        self.video_url = video_url
        self.error = error

class BaseProvider(ABC):
    @abstractmethod
    def submit(self, prompt: str, options: Dict) -> VideoJob: ...
    @abstractmethod
    def fetch(self, job_id: str) -> VideoJob: ...
