"""Orders Service

This microservice exposes an endpoint for administrators to list all
completed orders. The data is read from the same JSON file written by
checkout-service. This service is read‑only and does not modify the
orders file.

Endpoint:
    GET /api/orders → returns a list of all orders

To run locally:
    uvicorn main:app --reload --host 0.0.0.0 --port 8005
"""

import json
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Orders Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# The path to the orders JSON file. By default this points to the
# checkout-service's data directory, but it can be overridden via an
# environment variable. When deployed on Kubernetes the two services
# share a PersistentVolume so that this file is available in both pods.
ORDERS_FILE = os.getenv(
    "ORDERS_FILE",
    os.path.join(os.path.dirname(__file__), "..", "checkout-service", "data", "orders.json"),
)

@app.get("/api/orders")
async def list_orders():
    """Return all stored orders.

    If the file does not exist or cannot be read, an empty list is
    returned.
    """
    if not os.path.exists(ORDERS_FILE):
        return {"orders": []}
    try:
        with open(ORDERS_FILE, "r", encoding="utf-8") as f:
            orders = json.load(f)
    except Exception:
        orders = []
    return {"orders": orders}

@app.get("/healthz")
async def health() -> dict[str, str]:
    return {"status": "ok"}
