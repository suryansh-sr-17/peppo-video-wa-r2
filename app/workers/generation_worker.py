# app/workers/generation_worker.py

import os
import asyncio
import logging
from typing import Optional

from app.integrations.twilio import send_message, send_media
from app.services.jobs import JobStore
from app.workers.video_utils import downscale_video

log = logging.getLogger("workers.generation")

# Public base URL used for development (ngrok) so Twilio can fetch /video/{job_id}
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")

# Base URL of our API (for feedback endpoint). Default assumes same PUBLIC_BASE_URL.
API_BASE_URL = os.getenv("API_BASE_URL", PUBLIC_BASE_URL).rstrip("/")


async def process_whatsapp_job(job_id: str, user_number: str, video_gen, job_store: JobStore):
    """
    Background worker that polls the provider for job completion and sends
    the video back to the WhatsApp user via Twilio when ready.

    Parameters:
      - job_id: provider job id
      - user_number: e.g. "whatsapp:+1234567890"
      - video_gen: a VideoGenerator instance (passed by main to avoid circular imports)
      - job_store: the same JobStore instance used by the app
    """
    log.info("Worker started: job=%s -> %s", job_id, user_number)

    max_attempts = 60  # poll up to ~60 * backoff seconds
    attempt = 0
    backoff = 1.5

    while attempt < max_attempts:
        attempt += 1
        try:
            pj = video_gen.fetch(job_id)
        except Exception:
            log.exception("Error polling provider for job %s", job_id)
            pj = None

        if pj is None:
            # provider error while fetching — notify and stop
            try:
                send_message(user_number, "⚠️ Error checking generation status. Please try again later.")
            except Exception:
                log.exception("Failed to notify user about provider fetch error for job %s", job_id)
            return

        log.debug("Polled job %s status=%s", job_id, pj.status)

        if pj.status == "succeeded":
            rec = job_store.get(job_id)

            # Prefer public provider URL if available
            media_url = pj.video_url or (rec.meta.get("provider_output_url") if rec else None)

            # If we don't have a direct public URL, try to expose our local /video/{job_id}
            if not media_url:
                if rec and rec.video_path:
                    if PUBLIC_BASE_URL:
                        p = rec.video_path
                        if not p.startswith("/"):
                            p = "/" + p
                        media_url = f"{PUBLIC_BASE_URL}{p}"
                    else:
                        # cannot deliver media to Twilio without public base URL
                        log.warning("No PUBLIC_BASE_URL defined; cannot deliver media for job=%s", job_id)
                        try:
                            send_message(
                                user_number,
                                f"✅ Your video is ready but the server is not public. Open the app to view it (job: {job_id}).",
                            )
                        except Exception:
                            log.exception("Failed to notify user about local-only video for job %s", job_id)
                        return
                else:
                    # No video URL at all
                    try:
                        send_message(user_number, "⚠️ Video finished but URL missing. Please try again later.")
                    except Exception:
                        log.exception("Failed to notify user about missing URL for job %s", job_id)
                    return
                
            # --- Ensure WhatsApp-safe size (<16MB) ---
            compressed_dir = "app/static/compressed"
            os.makedirs(compressed_dir, exist_ok=True)

            # For demo we always compress placeholder; in real case use provider file path
            input_path = "app/static/placeholder.mp4"
            output_path = os.path.join(compressed_dir, f"{job_id}.mp4")

            try:
                downscale_video(input_path, output_path)
                # Update record + media_url to point to compressed file served via /video/{job_id}
                rec.video_path = f"/video/{job_id}"
                if PUBLIC_BASE_URL:
                    media_url = f"{PUBLIC_BASE_URL}{rec.video_path}"
            except Exception as e:
                log.exception("Video compression failed for job=%s: %s", job_id, e)

            # Prepare unified caption (video + feedback request)
            caption = (
                "✅ Here's your AI-generated video!\n\n"
                "🙏 Did you like it?\n"
                "Please reply with 👍 or 👎"
            )

            try:
                # --- DEVELOPMENT MODE (use link to save Twilio media quota) ---
                fallback = pj.video_url or media_url or f"/video/{job_id}"
                send_message(user_number, f"{caption}\n\n🔗 Video link: {fallback}")

                # --- DEMO MODE (uncomment this for real demo day) ---
                send_media(user_number, media_url, caption=caption)

                log.info("Sent video (dev link mode) for job %s -> %s", job_id, user_number)

                # 🔹 NEW: Mark this job as awaiting feedback
                job_store.mark_feedback_pending(job_id)

            except Exception:
                log.exception("Failed to send video for job=%s to %s", job_id, user_number)
            return

        if pj.status == "failed":
            err_msg = pj.error or "Generation failed"
            try:
                send_message(user_number, f"⚠️ Video generation failed: {err_msg}")
            except Exception:
                log.exception("Failed to notify user about failure for job=%s", job_id)
            return

        # still processing: optionally send a progress update after first poll
        if attempt == 2:
            try:
                send_message(user_number, "⏳ Still working — this can take ~30–90s. I'll message you when it's ready.")
            except Exception:
                log.debug("Could not send progress update to %s", user_number)

        await asyncio.sleep(backoff)

    # Timeout reached
    try:
        send_message(user_number, "⚠️ The generation is taking longer than expected. We'll notify you when it's ready.")
    except Exception:
        log.exception("Failed to send timeout message for job=%s", job_id)
