#!/usr/bin/env python3
# send_test_message.py
"""
Send a WhatsApp test message using Twilio.
Usage:
  python send_test_message.py --to whatsapp:+1234567890
Or set TWILIO_TEST_TO in your .env and run without args.
"""
import os
import sys
import argparse
from dotenv import load_dotenv
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

load_dotenv()

def main():
    parser = argparse.ArgumentParser(description="Send a WhatsApp test message via Twilio sandbox")
    parser.add_argument("--to", help="Recipient (E.164) e.g. whatsapp:+919433369696", default=None)
    parser.add_argument("--body", help="Message body", default="Hello 👋, this is a test message from Peppo AI WhatsApp bot!")
    args = parser.parse_args()

    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_whatsapp = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
    to_number = args.to or os.getenv("TWILIO_TEST_TO")

    if not account_sid or not auth_token:
        print("ERROR: TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN must be set in your environment or .env file.")
        sys.exit(2)

    if not to_number:
        print("ERROR: recipient number is required. Provide --to or set TWILIO_TEST_TO in .env (format: whatsapp:+1234567890).")
        sys.exit(2)

    # Ensure correct prefix
    if not to_number.startswith("whatsapp:"):
        to_number = f"whatsapp:{to_number}"

    try:
        client = Client(account_sid, auth_token)
    except Exception as e:
        print("ERROR: Failed to initialize Twilio client:", e)
        sys.exit(2)

    try:
        message = client.messages.create(
            from_=from_whatsapp,
            to=to_number,
            body=args.body
        )
        print("✅ Message sent! SID:", message.sid)
    except TwilioRestException as te:
        print("Twilio error:", te)
        sys.exit(3)
    except Exception as e:
        print("Unexpected error sending message:", e)
        sys.exit(4)

if __name__ == "__main__":
    main()
