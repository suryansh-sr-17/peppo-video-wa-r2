# app/integrations/twilio.py

import os
import logging
from dotenv import load_dotenv
from typing import Optional, Dict, Any
from twilio.rest import Client
from twilio.request_validator import RequestValidator
from twilio.twiml.messaging_response import MessagingResponse
from starlette.requests import Request

log = logging.getLogger("integrations.twilio")

# ---- Load environment variables early ----
load_dotenv()  # ensures .env values are loaded no matter where this file is imported

# ---- Configuration (from env) ----
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
TWILIO_STATUS_CALLBACK_URL = os.getenv("TWILIO_STATUS_CALLBACK_URL", "")
TWILIO_WEBHOOK_URL = os.getenv("TWILIO_WEBHOOK_URL", "")

_client: Optional[Client] = None


# ---- Client helper ----
def _client_or_raise() -> Client:
    """Return a cached Twilio REST client, or raise if creds missing."""
    global _client
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        raise RuntimeError("Twilio credentials missing (TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN).")
    if _client is None:
        _client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    return _client


def _normalize_to(to: str) -> str:
    """Ensure 'to' starts with 'whatsapp:' as Twilio expects."""
    to = (to or "").strip()
    return to if to.startswith("whatsapp:") else f"whatsapp:{to}"


# ---- Outbound messaging ----
def send_message(to: str, body: str, **kwargs: Any) -> str:
    """
    Send a WhatsApp text message.
    Returns the Message SID.
    """
    client = _client_or_raise()
    try:
        msg = client.messages.create(
            from_=TWILIO_WHATSAPP_FROM,
            to=_normalize_to(to),
            body=(body or "")[:1600],  # WA text practical limit
            status_callback=TWILIO_STATUS_CALLBACK_URL or None,
            **kwargs,
        )
        return msg.sid
    except Exception as e:
        log.exception("Error sending Twilio message")
        raise


def send_media(to: str, media_url: str, caption: Optional[str] = None, **kwargs: Any) -> str:
    """
    Send a WhatsApp media message (e.g., video). media_url must be publicly accessible HTTPS.
    Returns the Message SID.
    """
    client = _client_or_raise()
    try:
        msg = client.messages.create(
            from_=TWILIO_WHATSAPP_FROM,
            to=_normalize_to(to),
            body=(caption or None),
            media_url=[media_url],
            status_callback=TWILIO_STATUS_CALLBACK_URL or None,
            **kwargs,
        )
        return msg.sid
    except Exception:
        log.exception("Error sending Twilio media")
        raise


# ---- Inbound webhook helpers ----
async def parse_incoming(request: Request) -> Dict[str, str]:
    """
    Parse Twilio's inbound webhook (x-www-form-urlencoded).
    Returns dict with: from, body, wa_id, sid, raw
    """
    form = await request.form()
    data = {k: str(v) for k, v in form.items()}
    return {
        "from": data.get("From", ""),       # e.g. 'whatsapp:+1...'
        "body": (data.get("Body") or "").strip(),
        "wa_id": data.get("WaId", ""),      # Numeric WA ID Twilio provides
        "sid": data.get("MessageSid", ""),
        "raw": data,
    }


async def validate_request(request: Request, expected_url: Optional[str] = None) -> bool:
    """
    Validate X-Twilio-Signature using Twilio's RequestValidator.
    IMPORTANT: The URL used here must MATCH the URL configured in Twilio Console.
    If behind a proxy, set TWILIO_WEBHOOK_URL to the public URL.
    """
    if not TWILIO_AUTH_TOKEN:
        log.debug("TWILIO_AUTH_TOKEN not set; skipping request validation.")
        return True

    validator = RequestValidator(TWILIO_AUTH_TOKEN or "")
    signature = request.headers.get("X-Twilio-Signature", "")
    url_to_validate = (expected_url or TWILIO_WEBHOOK_URL or str(request.url))
    form = await request.form()
    params = {k: str(v) for k, v in form.items()}
    try:
        ok = validator.validate(url_to_validate, params, signature)
        if not ok:
            log.warning("Twilio signature validation failed for url=%s", url_to_validate)
        return ok
    except Exception:
        log.exception("Exception during Twilio signature validation")
        return False


def ack_twiml(text: str) -> str:
    """
    Create a TwiML XML string for an immediate WhatsApp reply (ack).
    Return this as Response(content=ack_twiml(...), media_type="application/xml")
    """
    resp = MessagingResponse()
    resp.message(text)
    return str(resp)
