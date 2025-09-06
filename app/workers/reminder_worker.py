# app/workers/reminder_worker.py
import asyncio
import logging
from app.integrations.twilio import send_message

log = logging.getLogger("app.reminder_worker")

# Keep track of scheduled reminder tasks per user
_reminder_tasks = {}

REMINDER_INTERVAL = 15  # seconds (demo)

async def _reminder_loop(user_number: str, job_store):
    try:
        while True:  # keep looping
            await asyncio.sleep(REMINDER_INTERVAL)
            if user_number in _reminder_tasks:
                last_job = job_store.get_last_job_for_user(user_number)
                if last_job and last_job.style:
                    # Take first 30 characters of prompt (or fewer if shorter)
                    prompt_snippet = (last_job.prompt[:15] + "...") if last_job.prompt and len(last_job.prompt) > 30 else (last_job.prompt or "your idea")
                    style_name = last_job.style.title()

                    msg = (
                        f"👋 Hey! Remember your last video on \"{prompt_snippet}\" "
                        f"with the {style_name} style?\n"
                        f"Want me to whip up another one? 🚀\n"
                        f"What are we waiting for!!!"
                    )
                else:
                    msg = (
                        "👋 Hey champ, it’s been a while since we made a video.\n"
                        "Got a new idea for me? 🎥✨"
                    )
                send_message(user_number, msg)
    except asyncio.CancelledError:
        log.info(f"Reminder for {user_number} cancelled (user active again)")
        raise


def schedule_reminder(user_number: str, job_store):
    """Start or restart a periodic reminder for the user."""
    cancel_reminder(user_number)  # cancel any existing one
    task = asyncio.create_task(_reminder_loop(user_number, job_store))
    _reminder_tasks[user_number] = task


def cancel_reminder(user_number: str):
    """Cancel a scheduled reminder if one exists."""
    task = _reminder_tasks.pop(user_number, None)
    if task and not task.done():
        task.cancel()
