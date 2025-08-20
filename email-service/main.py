"""
Email Service

Receives email payloads from checkout-service and sends them
either via SMTP (if configured) or simulates by printing to stdout.

Run locally:
    uvicorn main:app --host 127.0.0.1 --port 8004
"""

import os
import smtplib
import ssl
from email.message import EmailMessage
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Email Service")

# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------
SMTP_HOST = os.getenv("SMTP_HOST")            # e.g. smtp.office365.com / smtp.gmail.com
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")            # username/login
SMTP_PASS = os.getenv("SMTP_PASS")            # app password / SMTP password
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@university.edu")
FROM_NAME = os.getenv("FROM_NAME", "University Card Service Auto-Mail")

# -----------------------------------------------------------------------------
# Model
# -----------------------------------------------------------------------------
class EmailPayload(BaseModel):
    to: str
    subject: str
    body: str

# -----------------------------------------------------------------------------
# Send logic
# -----------------------------------------------------------------------------
def send_email(to_addr: str, subject: str, body: str):
    """Send email via SMTP if configured, otherwise simulate."""
    if SMTP_HOST and SMTP_USER and SMTP_PASS:
        msg = EmailMessage()
        msg["From"] = f"{FROM_NAME} <{FROM_EMAIL}>"
        msg["To"] = to_addr
        msg["Subject"] = subject
        msg.set_content(body)

        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls(context=context)
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)

        print(f"[email-service] Sent real email to {to_addr}")
        return {"status": "sent", "to": to_addr}
    else:
        print("----- Simulated Email -----")
        print(f"To: {to_addr}")
        print(f"From: {FROM_NAME} <{FROM_EMAIL}>")
        print(f"Subject: {subject}")
        print(body)
        print("----- End Email -----")
        return {"status": "simulated", "to": to_addr}

# -----------------------------------------------------------------------------
# Endpoint
# -----------------------------------------------------------------------------
@app.post("/api/email")
def send_email_api(payload: EmailPayload):
    return send_email(payload.to, payload.subject, payload.body)

@app.get("/healthz")
async def health() -> dict[str, str]:
    return {"status": "ok"}

