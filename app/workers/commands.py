# app/workers/commands.py

"""
Command handlers for the WhatsApp bot.
These return text strings that the webhook will wrap into TwiML via ack_twiml().
"""

from typing import List
from app.services.jobs import JobStore

def handle_guide() -> str:
    return (
        "📖 *Peppo AI Guide*\n\n"
        "Commands you can use:\n"
        "• `/guide` – Show this help message\n"
        "• `/status` – Check your last video generation status\n"
        "• `/history` – View your recent requests\n\n"
        "Or simply send me a prompt and I’ll generate a short video!"
    )

def handle_status(user_number: str, job_store: JobStore, video_gen) -> str:
    """
    Return a one-line friendly status message for the user's most recent job.
    """
    rec = job_store.get_last_job_for_user(user_number)
    if not rec:
        return "ℹ️ You don’t have any recent jobs. Send me a prompt to start!"

    # fetch latest status from provider
    try:
        pj = video_gen.fetch(rec.job_id)
        status = pj.status
    except Exception:
        # fall back to the stored record
        status = rec.status

    # friendly formatting
    if status == "succeeded":
        video_link = rec.video_path or rec.meta.get("provider_output_url") or ""
        return f"✅ Job `{rec.job_id}` finished!\nVideo: {video_link or '[no public URL]'}"
    elif status == "failed":
        return f"❌ Job `{rec.job_id}` failed. Try again or send a different prompt."
    else:
        return f"⏳ Job `{rec.job_id}` is still {status} — hang tight!"

def handle_history(user_number: str, job_store: JobStore, limit: int = 5) -> str:
    """
    Return a short history summary for the user listing the most recent jobs.
    Uses JobRecord fields: created_at, job_id, status, prompt, video_path.
    """
    recs = job_store.get_history_for_user(user_number, limit=limit)
    if not recs:
        return "ℹ️ No history yet. Send me a prompt and I'll create your first video!"

    lines: List[str] = []
    for r in recs:
        ts = r.created_at or ""
        ts_short = ts.replace("T", " ").replace("Z", "")[:16] if ts else "unknown"
        prompt_short = (r.prompt or "")[:60].replace("\n", " ")
        style_txt = f" [{r.style}]" if getattr(r, "style", None) else ""

        # status → emoji
        if r.status == "succeeded" and (r.video_path or r.meta.get("provider_output_url")):
            flag = "✅"
        elif r.status == "processing":
            flag = "⏳"
        elif r.status == "failed":
            flag = "⚠️"
        else:
            flag = ""

        # choose link if available
        video_link = ""
        if r.status == "succeeded":
            video_link = r.video_path or r.meta.get("provider_output_url") or ""

        line = f"{ts_short} | {r.job_id[:8]} | {flag} {r.status} | {prompt_short} | {style_txt}"
        if video_link:
            line += f"\n   🔗 {video_link}"

        lines.append(line)

    return "📜 Your recent jobs (newest first):\n\n" + "\n\n".join(lines)
