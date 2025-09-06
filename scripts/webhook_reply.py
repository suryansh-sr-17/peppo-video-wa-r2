#!/usr/bin/env python3
# webhook_reply.py
"""
Simple Flask webhook that replies to WhatsApp messages with a TwiML ack.
Designed for quick dev with ngrok + Twilio Sandbox.
"""
import os
import logging
from dotenv import load_dotenv
from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse

load_dotenv()

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("webhook_reply")

app = Flask(__name__)

@app.route("/healthz", methods=["GET"])
def healthz():
    return "ok", 200

@app.route("/webhook/whatsapp", methods=["POST"])
def whatsapp_webhook():
    # ⚠️ Skipping Twilio signature validation for demo
    # This ensures no 403 errors from signature mismatch

    incoming_msg = request.form.get("Body", "").strip()
    from_number = request.form.get("From", "")
    msg_sid = request.form.get("MessageSid", "")

    log.info("📩 Incoming message from %s (sid=%s): %s", from_number, msg_sid, incoming_msg)
    log.debug("Raw form: %s", request.form.to_dict(flat=True))

    # Build a response (TwiML)
    resp = MessagingResponse()
    if incoming_msg:
        resp.message(f"✅ Got your message: {incoming_msg}")
    else:
        resp.message("❌ Empty message received. Send a prompt to generate a video.")

    return Response(str(resp), mimetype="text/xml")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    host = os.environ.get("HOST", "0.0.0.0")
    log.info("Starting webhook_reply on %s:%s (signature validation disabled)", host, port)
    app.run(host=host, port=port)
