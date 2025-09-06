# app/main.py

import os
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, Tuple
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.services.prompts import compose_prompt, prompt_hash
from app.services.jobs import JobStore, JobRecord
from app.services.video_generator import VideoGenerator
from app.services.prompt_optimizer import optimize_prompt
from app.services.feedback import save_feedback
from app.workers.generation_worker import process_whatsapp_job
from app.workers.commands import handle_guide, handle_status, handle_history
from app.services.requests import RequestQueue
from app.workers.reminder_worker import schedule_reminder, cancel_reminder

# Twilio helpers (send_message/send_media + webhook parsing)
from app.integrations.twilio import (
    parse_incoming,
    ack_twiml,
    validate_request,
    send_message,
)


log = logging.getLogger("app.main")
logging.basicConfig(level=logging.INFO)

APP_ORIGIN = os.getenv("APP_ORIGIN", "*")
PROVIDER_NAME = os.getenv("VIDEO_PROVIDER", "mock").lower()
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    asyncio.create_task(process_queue())
    try:
        dev_number = os.getenv("TWILIO_TEST_TO")
        if dev_number:
            intro_msg = (
                "👋 Hello! I’m Peppo AI Video Bot.\n\n"
                "Send me a text prompt and I’ll turn it into a video 🎥✨\n"
                "Type /help anytime to see what I can do."
            )
            # schedule async send
            asyncio.create_task(_send_intro(dev_number, intro_msg))
    except Exception as e:
        log.error(f"Failed to send intro message: {e}")
    yield


async def _send_intro(dev_number: str, intro_msg: str):
    try:
        send_message(dev_number, intro_msg)   # Twilio send
        log.info(f"✅ Sent intro message to {dev_number}")
    except Exception as e:
        log.error(f"Intro message error: {e}")

app = FastAPI(
    title="Peppo AI – Video Generator",
    version="1.2",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[APP_ORIGIN] if APP_ORIGIN != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

STYLE_ALIASES = {
    "anime": "anime", "✨": "anime", "Anime": "anime",
    "cartoon": "cartoon", "🎭": "cartoon", "Cartoon": "cartoon",
    "cyberpunk": "cyberpunk", "🤖": "cyberpunk", "Cyberpunk": "cyberpunk",
}

# single job_store instance used by main & passed to worker
job_store = JobStore()
video_gen = VideoGenerator(PROVIDER_NAME, job_store=job_store)
request_queue = RequestQueue()   # ✅ new queue for multiple requests

# Minimum length for a prompt before showing warning
MIN_PROMPT_LENGTH = 12  # characters

@app.get("/healthz")
def healthz():
    return {"ok": True, "provider": PROVIDER_NAME}


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# ---------------------------
# Update: /generate endpoint
# ---------------------------
@app.post("/generate")
async def generate(payload: dict):
    user_prompt = (payload.get("prompt") or "").strip()
    style = (payload.get("style") or "cinematic").strip().lower()
    if not user_prompt:
        raise HTTPException(400, "Prompt is required")

    created_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    # ✅ Step 1: enqueue the request instead of generating immediately
    
    req_id = request_queue.enqueue("api-user", user_prompt, style=style)

    return {
        "request_id": req_id,
        "status": "queued",
        "message": "Your request has been added to the queue. It will be processed soon.",
        "prompt": user_prompt,
        "style": style,
        "created_at": created_at,
    }


@app.get("/status/{job_id}")
async def status(job_id: str):
    pj = video_gen.fetch(job_id)
    rec = job_store.get(job_id)
    if not rec:
        raise HTTPException(404, "Job not found")

    rec.status = pj.status
    if pj.status == "succeeded" and not rec.video_path:
        rec.video_path = f"/video/{job_id}"
        if pj.video_url:
            rec.meta["provider_output_url"] = pj.video_url

    # NEW: persist status update into DB
    job_store.update_status_in_db(job_id, rec.status, rec.video_path)

    if pj.error:
        return {"job_id": job_id, "status": "failed", "error": pj.error}

    return {
        "job_id": job_id,
        "status": rec.status,
        "video_url": rec.video_path,
        "cached": rec.cached,
    }


def _parse_range(range_header: Optional[str], file_size: int) -> Optional[Tuple[int, int]]:
    if not range_header or "=" not in range_header:
        return None
    units, rng = range_header.split("=", 1)
    if units.strip().lower() != "bytes":
        return None
    start_s, _, end_s = rng.partition("-")
    try:
        if start_s and end_s:
            start, end = int(start_s), int(end_s)
        elif start_s:
            start, end = int(start_s), file_size - 1
        else:
            n = int(end_s)
            start, end = file_size - n, file_size - 1
        if start < 0 or end >= file_size or start > end:
            return None
        return (start, end)
    except ValueError:
        return None


@app.get("/video/{job_id}")
def video(job_id: str, request: Request):
    compressed_path = f"app/static/compressed/{job_id}.mp4"
    # Serve compressed video if available, else fallback to placeholder
    path = compressed_path if os.path.exists(compressed_path) else "app/static/placeholder.mp4"

    if not os.path.exists(path):
        raise HTTPException(404, "Video missing")

    file_size = os.path.getsize(path)
    range_header = request.headers.get("range")
    rng = _parse_range(range_header, file_size)

    def iterfile(start: int = 0, end: int = file_size - 1, chunk_size: int = 64 * 1024):
        with open(path, "rb") as f:
            f.seek(start)
            bytes_left = end - start + 1
            while bytes_left > 0:
                chunk = f.read(min(chunk_size, bytes_left))
                if not chunk:
                    break
                bytes_left -= len(chunk)
                yield chunk

    if rng:
        start, end = rng
        headers = {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(end - start + 1),
        }
        return StreamingResponse(iterfile(start, end), status_code=206, headers=headers, media_type="video/mp4")

    headers = {"Accept-Ranges": "bytes", "Content-Length": str(file_size)}
    return StreamingResponse(iterfile(), headers=headers, media_type="video/mp4")


@app.post("/optimize_prompt")
async def optimize(payload: dict):
    user_prompt = (payload.get("prompt") or "").strip()
    style = (payload.get("style") or "cinematic").strip().lower()

    if not user_prompt:
        raise HTTPException(400, "Prompt is required")

    optimized = optimize_prompt(user_prompt, style)
    return {"optimized_prompt": optimized}


# ---------------------------
# WhatsApp webhook endpoint
# ---------------------------
@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    # optional signature validation (will skip if no TWILIO_AUTH_TOKEN is set)
    valid = await validate_request(request)
    if not valid:
        # for dev/demo we continue but log so you can enable/disable validation
        log.warning("Invalid Twilio signature – continuing anyway (dev demo mode)")

    data = await parse_incoming(request)  # from app/integrations/twilio.py
    user_number = data["from"]
    user_msg = (data["body"] or "").strip()

    # Cancel any pending inactivity reminder since user is active again
    cancel_reminder(user_number)

    log.info("WhatsApp incoming from %s: %s", user_number, user_msg)

    # If empty message
    if not user_msg:
        return Response(ack_twiml("❌ Please send a valid prompt."), media_type="application/xml")

    # Normalize command text
    msg = user_msg.lower().strip()

    # --- Help/Guide ---
    if msg in ("/help", "help", "/guide", "guide"):
        guide_text = handle_guide()
        return Response(ack_twiml(guide_text), media_type="application/xml")

    # --- Status command (last job) ---
    if msg in ("/status", "status"):
        status_text = handle_status(user_number, job_store, video_gen)
        return Response(ack_twiml(status_text), media_type="application/xml")

    # --- History command (recent N jobs) ---
    if msg in ("/history", "history"):
        history_text = handle_history(user_number, job_store)
        return Response(ack_twiml(history_text), media_type="application/xml")
    
    # --- Check if user is choosing a style ---
    pending = job_store.get_pending_prompt(user_number)
    if pending and pending.awaiting_style:
        chosen = STYLE_ALIASES.get(msg)
        if not chosen:
            return Response(ack_twiml("⚠️ Please choose a valid style: anime(✨), cartoon(🎭), or cyberpunk(🤖)."),
                            media_type="application/xml")

         # Update record with chosen style
        pending.awaiting_style = False
        pending.chosen_style = chosen

        # --- ✅ NEW: Cache check before submitting a new job ---
        h = prompt_hash(pending.prompt, chosen)
        cached = job_store.get_by_hash(h)
        if cached and cached.status == "succeeded":
            # Use existing video from cache
            if cached.video_path:
                video_url = f"{PUBLIC_BASE_URL}{cached.video_path}" if PUBLIC_BASE_URL else cached.video_path
                cache_msg = f"✅ Video fetched from cache!\n\n🔗 {video_url}"
                return Response(ack_twiml(cache_msg), media_type="application/xml")

        # --- Prompt length check ---
        warning_text = ""
        if len(pending.prompt.strip()) < MIN_PROMPT_LENGTH:
            warning_text = (
                "⚠️ Your prompt is a bit short.\n"
                "Next time make sure to have a longer prompt.\n"
                "Don't worry — prompt optimizing is on us. ✅\n\n"
            )

        # --- Optimize the prompt ---
        try:
            final_prompt = optimize_prompt(pending.prompt, chosen)
        except Exception:
            final_prompt = pending.prompt

        # --- Construct acknowledgement message ---
        ack_text = (
            f"{warning_text}"
            f"✅ Got it! Generating a video for: optimized prompt for [ {final_prompt} in {chosen} style ]"
        )
        response_xml = ack_twiml(ack_text)

        created_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        job = video_gen.submit(final_prompt, style=chosen)
        rec = JobRecord(
            job_id=job.job_id,
            status=job.status,
            video_path=None,
            provider=PROVIDER_NAME,
            prompt_hash=prompt_hash(pending.prompt, chosen),
            prompt=pending.prompt,
            final_prompt=final_prompt,
            created_at=created_at,
            style=chosen,         # <--- persist the chosen style here
            chosen_style=chosen,  # <--- keep chosen_style for in-memory record
        )
        job_store.put(rec, user_id=user_number)
        job_store.store_user_job(user_number, job.job_id)

        asyncio.create_task(process_whatsapp_job(job.job_id, user_number, video_gen, job_store))
        return Response(response_xml, media_type="application/xml")
    
    # --- Feedback flow ---
    last_job = job_store.get_last_job_for_user(user_number)
    if last_job and last_job.feedback_pending:
        if msg in ("👍", "👍🏻", "👍🏼", "👍🏽", "👍🏾", "👍🏿"):  # thumbs up variants
            save_feedback(last_job.job_id, last_job.prompt or "(unknown)", True)
            job_store.mark_feedback_received(last_job.job_id, True)
            schedule_reminder(user_number, job_store)
            return Response(ack_twiml("🙏 Thanks for your positive feedback!"), media_type="application/xml")

        elif msg in ("👎", "👎🏻", "👎🏼", "👎🏽", "👎🏾", "👎🏿"):  # thumbs down variants
            save_feedback(last_job.job_id, last_job.prompt or "(unknown)", False)
            job_store.mark_feedback_received(last_job.job_id, False)
            schedule_reminder(user_number, job_store)
            return Response(ack_twiml("🙏 Thanks for your feedback! We'll keep improving."), media_type="application/xml")

        else:
            return Response(ack_twiml("⚠️ Please reply with 👍 or 👎 to give feedback before generating a new video."), media_type="application/xml")
        

    # --- Otherwise treat as new prompt: ask for style first ---
    # Save prompt temporarily, mark as awaiting style
    job_store.set_pending_prompt(user_number, user_msg)

    style_prompt = (
        "Nice prompt you got there buddy.\n\n"
        "Choose your art style 🎨:\n"
        "• Anime (✨)\n"
        "• Cartoon (🎭)\n"
        "• Cyberpunk (🤖)"
    )
    return Response(ack_twiml(style_prompt), media_type="application/xml")

async def process_queue():
    while True:
        req = request_queue.dequeue()
        if not req:
            await asyncio.sleep(2)
            continue

        try:
            final_prompt = compose_prompt(req.prompt, req.style)
            job = video_gen.submit(final_prompt, style=req.style)
            request_queue.mark_processing(req.id, job.job_id)

            rec = JobRecord(
                job_id=job.job_id,
                status=job.status,
                video_path=None,
                provider=PROVIDER_NAME,
                prompt_hash=prompt_hash(req.prompt, req.style),
                prompt=req.prompt,
                final_prompt=final_prompt,
                created_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                style=req.style,
                chosen_style=req.style,
            )
            job_store.put(rec, user_id=req.user_id)

            asyncio.create_task(process_whatsapp_job(job.job_id, req.user_id, video_gen, job_store))
            request_queue.mark_done(req.id, success=True)

        except Exception as e:
            log.error(f"Queue processing failed for request {req.id}: {e}")
            request_queue.mark_done(req.id, success=False)


@app.post("/feedback")
async def feedback(payload: dict):
    job_id = payload.get("job_id")
    prompt = payload.get("prompt")
    liked = payload.get("liked")

    if not job_id or prompt is None or liked is None:
        raise HTTPException(400, "job_id, prompt and liked are required")

    # Save feedback
    res = save_feedback(job_id, prompt, bool(liked))

    # Look up the job to get the user’s number
    rec = job_store.get(job_id)
    if rec and rec.user_number:
        try:
            msg = "🙏 Thanks for your feedback! It helps us improve."
            send_message(rec.user_number, msg)
        except Exception as e:
            raise HTTPException(500, f"Feedback saved but failed to notify user: {str(e)}")

    return {"status": "ok", "saved": res}
