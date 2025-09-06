# app/providers/modelslab.py

import time
import logging
import requests
from typing import Dict, Optional
from .base import BaseProvider, VideoJob

class ModelsLabProvider(BaseProvider):
    """
    Adapter that exposes a BaseProvider interface over the Stable Diffusion
    (ModelsLab) API directly using `requests`.

    For the demo, we still always return 'processing' first and let the frontend
    show the static placeholder.mp4. Real API responses are cached internally.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or "DEMO_KEY"  # replace with real key if available
        self.api_url = "https://api.modelslab.com/v1/video"  # example endpoint
        self._jobs: Dict[str, Dict] = {}  # job_id -> {"fetch_url":..., "output_url":..., "status":...}
        self.log = logging.getLogger("provider.modelslab")

    def submit(self, prompt: str, options: Dict) -> VideoJob:
        overrides = self._style_overrides(options.get("style")) if options else {}

        try:
            payload = {
                "prompt": prompt,
                **overrides
            }
            headers = {"Authorization": f"Bearer {self.api_key}"}

            resp = requests.post(self.api_url + "/text2video", json=payload, headers=headers)
            resp.raise_for_status()
            resp_json = resp.json()

        except Exception as e:
            self.log.exception("Error submitting job to ModelsLab")
            return VideoJob(job_id="n/a", status="failed", error=str(e))

        if resp_json.get("status") == "error":
            return VideoJob(job_id="n/a", status="failed", error=resp_json.get("message"))

        # Ensure job_id
        job_id = resp_json.get("id") or str(int(time.time() * 1000))
        self._jobs[job_id] = {
            "fetch_url": resp_json.get("fetch_url"),
            "output_url": resp_json.get("output_url"),
            "status": resp_json.get("status"),
        }

        return VideoJob(job_id=job_id, status="processing")

    def fetch(self, job_id: str) -> VideoJob:
        data = self._jobs.get(job_id)
        if not data:
            return VideoJob(job_id, status="not_found", error="Unknown job")

        # Cached success
        if data.get("status") == "succeeded":
            return VideoJob(job_id, status="succeeded", video_url=data.get("output_url"))

        fetch_url = data.get("fetch_url")
        if not fetch_url and data.get("output_url"):
            data["status"] = "succeeded"
            return VideoJob(job_id, status="succeeded", video_url=data.get("output_url"))

        # Poll provider
        if fetch_url:
            try:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                resp = requests.get(fetch_url, headers=headers)
                resp.raise_for_status()
                resp_json = resp.json()
            except Exception as e:
                self.log.exception("Error fetching job result")
                return VideoJob(job_id, status="failed", error=str(e))

            status = resp_json.get("status")
            if status == "processing":
                return VideoJob(job_id, status="processing")
            elif status in ("success", "succeeded"):
                out = resp_json.get("output_url")
                data["output_url"] = out
                data["status"] = "succeeded"
                return VideoJob(job_id, status="succeeded", video_url=out)
            else:
                return VideoJob(job_id, status="failed", error=resp_json.get("message") or "provider_error")

        return VideoJob(job_id, status="processing")

    def _style_overrides(self, style: Optional[str]) -> Dict:
        """Optional gentle tuning based on 'style' selection."""
        if not style:
            return {}
        s = style.lower()
        if s == "cinematic":
            return {"fps": 24, "num_frames": 24, "guidance_scale": 6.5}
        if s == "anime":
            return {"fps": 16, "num_frames": 20, "guidance_scale": 7.5}
        if s == "product":
            return {"fps": 20, "num_frames": 16, "guidance_scale": 6.0}
        return {}
