"""
Checkout Service

Accepts completed orders from the frontend, persists them to disk, and
triggers the email-service to send confirmation emails to both the
customer and the administrator.

Run locally:
    uvicorn main:app --host 127.0.0.1 --port 8003
"""

import json
import os
import threading
from typing import List

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# -----------------------------------------------------------------------------
# App & CORS
# -----------------------------------------------------------------------------
app = FastAPI(title="Checkout Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for local dev; tighten in prod (e.g., ["http://localhost:8080"])
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------
ORDERS_FILE = os.getenv(
    "ORDERS_FILE",
    os.path.join(os.path.dirname(__file__), "data", "orders.json"),
)

# Where to POST a single email: expects {to, subject, body}
EMAIL_ENDPOINT = os.getenv("EMAIL_ENDPOINT", "http://localhost:8004/api/email")

# Admin contact (receives a copy/notification)
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "mangeshg1408@gmail.com")

# Optional footer branding in emails
FROM_NAME = os.getenv("FROM_NAME", "University Card Authority")

# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------
class Customer(BaseModel):
    student_id: str = Field(..., alias="id")
    name: str
    institute: str
    phone: str
    email: str
    room: str

class OrderItem(BaseModel):
    item_id: int
    template_id: str
    student_id: str
    name: str
    institute: str
    phone: str
    email: str
    room: str

class OrderRequest(BaseModel):
    customer: Customer
    items: List[OrderItem]

# -----------------------------------------------------------------------------
# Persistence helpers
# -----------------------------------------------------------------------------
def load_orders() -> List[dict]:
    """Load existing orders from JSON file."""
    if os.path.exists(ORDERS_FILE):
        try:
            with open(ORDERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_orders(orders: List[dict]) -> None:
    """Save all orders to JSON file."""
    os.makedirs(os.path.dirname(ORDERS_FILE), exist_ok=True)
    with open(ORDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)

# -----------------------------------------------------------------------------
# Email helpers
# -----------------------------------------------------------------------------
def _post_email(to_addr: str, subject: str, body: str) -> None:
    """POST a single email payload to the email-service. Logs errors but
    does not raise, so checkout flow isn't blocked."""
    try:
        resp = requests.post(
            EMAIL_ENDPOINT,
            json={"to": to_addr, "subject": subject, "body": body},
            timeout=8,
        )
        resp.raise_for_status()
        print(f"[checkout] Email queued → {to_addr}: {subject}")
    except Exception as e:
        print(f"[checkout] Email send failed to {to_addr}: {e}")

def send_customer_and_admin_emails(order: dict) -> None:
    """Build and send the customer confirmation + admin notification."""
    cust = order["customer"]
    cust_name = cust.get("name", "")
    cust_email = cust.get("email", "")
    order_id = order.get("order_id")
    items = order.get("items", [])

    # Customer email
    cust_subject = f"Your RFID business card order #{order_id}"
    cust_body = (
        f"Hello {cust_name},\n\n"
        f"Thank you for ordering your RFID-enabled business card.\n"
        f"Your order ID is {order_id}. We will process your request and notify you once it is ready.\n\n"
        f"Regards,\n{FROM_NAME}"
    )

    # Admin email
    admin_subject = f"New RFID card order #{order_id}"
    admin_body = (
        "A new RFID business card order has been placed.\n"
        f"Order ID: {order_id}\n"
        f"Customer: {cust_name} ({cust_email})\n"
        f"Number of items: {len(items)}\n"
        "Please log into the admin portal to view full details."
    )

    # Fire-and-forget in a background thread (non-blocking)
    def _worker():
        if cust_email:
            _post_email(cust_email, cust_subject, cust_body)
        if ADMIN_EMAIL:
            _post_email(ADMIN_EMAIL, admin_subject, admin_body)

    threading.Thread(target=_worker, daemon=True).start()

# -----------------------------------------------------------------------------
# Endpoint
# -----------------------------------------------------------------------------
@app.post("/api/checkout")
async def checkout_order(order_request: OrderRequest):
    """Accept an order, persist it, and trigger two emails (customer + admin)."""
    # Build order dict with sequential ID
    orders = load_orders()
    next_id = (orders[-1]["order_id"] + 1) if orders else 1
    order = {
        "order_id": next_id,
        "customer": order_request.customer.dict(by_alias=True),
        "items": [item.dict() for item in order_request.items],
    }

    # Persist
    orders.append(order)
    try:
        save_orders(orders)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to persist order: {exc}")

    # Trigger emails (non-blocking)
    send_customer_and_admin_emails(order)

    return {"status": "success", "order_id": next_id}

@app.get("/healthz")
async def health() -> dict[str, str]:
    return {"status": "ok"}
