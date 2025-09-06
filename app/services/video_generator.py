# app/services/video_generator.py
import logging
import datetime
from typing import Optional, Dict, Any
from app.services.jobs import JobRecord, JobStore
from app.services.prompts import compose_prompt, prompt_hash
from app.providers.base import BaseProvider
from app.providers.mock import MockProvider
from app.providers.modelslab import ModelsLabProvider

log = logging.getLogger("services.video_generator")

def _build_provider() -> BaseProvider:
    """Factory to select provider based on env or fallback to mock."""
    # keep lightweight factory (can be overridden)
    # Note: don't import os here for clarity; main already determines provider by passing string
    return MockProvider()

class VideoGenerator:
    """
    Handles video generation lifecycle across providers.

    IMPORTANT: Accepts a JobStore instance so state is shared with app.main and workers.
    """

    def __init__(self, provider: Optional[Any] = None, job_store: Optional[JobStore] = None):
        # provider can be a string ("modelslab"/"mock"), a provider instance, or None
        if isinstance(provider, str):
            self.provider = ModelsLabProvider() if provider == "modelslab" else MockProvider()
        else:
            self.provider = provider or _build_provider()

        # Use shared JobStore if provided; otherwise create a local one (warning logged).
        if job_store is None:
            self.job_store = JobStore()
            log.warning("VideoGenerator created without shared job_store — this may cause state divergence.")
        else:
            self.job_store = job_store

        log.debug("VideoGenerator initialized with provider=%s job_store_id=%s", type(self.provider).__name__, id(self.job_store))

    def submit(
        self,
        user_prompt: str,
        style: str = "cinematic",
        options: Optional[Dict[str, Any]] = None,
    ):
        """
        Submit a video generation request.
        Uses the shared self.job_store for caching/persistence.
        Returns provider-specific job object (which has job_id, status, etc).
        """
        if not user_prompt.strip():
            raise ValueError("Prompt is required")

        h = prompt_hash(user_prompt, style)
        cached = self.job_store.get_by_hash(h)

        if cached and cached.status == "succeeded":
            # Return JobRecord cached result (keeps compatibility with caller expectations)
            log.info("Returning cached job for hash=%s (job=%s)", h, cached.job_id)
            return cached

        # Compose final prompt and send to provider
        final_prompt = compose_prompt(user_prompt, style)
        job = self.provider.submit(final_prompt, options={"style": style, **(options or {})})

        # Persist record in the shared JobStore
        rec = JobRecord(
            job_id=job.job_id,
            status=job.status,
            video_path=None,
            provider=type(self.provider).__name__.lower(),
            prompt_hash=h,
            prompt=user_prompt,                # store final prompt into record
            final_prompt=user_prompt,
            created_at=datetime.datetime.utcnow().isoformat() + "Z",
            style=style,                       # persist style for provider-submitted rec
            chosen_style=style,
        )
        self.job_store.put(rec)
        log.debug("Submitted job=%s status=%s stored in job_store_id=%s", job.job_id, job.status, id(self.job_store))
        return job

    def fetch(self, job_id: str):
        """
        Check job status and update store.
        Returns provider job with latest status.
        """
        pj = self.provider.fetch(job_id)
        rec = self.job_store.get(job_id)

        if not rec:
            # No record in store; return provider job directly
            log.debug("fetch(): no JobRecord for job_id=%s in shared store", job_id)
            return pj

        # Update record status
        rec.status = pj.status
        if pj.status == "succeeded" and not rec.video_path:
            # expose internal app path that the /video/{job_id} route will serve
            rec.video_path = f"/video/{job_id}"
            if pj.video_url:
                rec.meta["provider_output_url"] = pj.video_url
            log.debug("fetch(): marked rec.video_path=%s for job=%s", rec.video_path, job_id)

        return pj
