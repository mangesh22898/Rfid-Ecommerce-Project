"""Cart Service

This microservice maintains a simple in‑memory shopping cart. It exposes
endpoints for listing items currently in the cart, adding a new item to the
cart and removing an existing item. The cart is not persisted across
service restarts – this design is intentional for the prototype stage. In a
production system you would store the cart in a database or a cache like
Redis keyed off the user's session.

Endpoints:
    GET    /api/cart            → returns all cart items
    POST   /api/cart            → add a new item (expects JSON body)
    DELETE /api/cart/{item_id}  → remove item by its generated identifier

To run locally:
    uvicorn main:app --reload --host 0.0.0.0 --port 8002
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

app = FastAPI(title="Cart Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic model describing the payload required to add an item to the cart.
class CartItemRequest(BaseModel):
    template_id: str
    student_id: str
    name: str
    institute: str
    phone: str
    email: str
    room: str

# We augment each item with an internal item_id to allow deletion.
class CartItem(BaseModel):
    item_id: int
    template_id: str
    student_id: str
    name: str
    institute: str
    phone: str
    email: str
    room: str

# In‑memory storage for cart items. In a real system this would be backed
# by a persistent store and keyed by user/session.
cart_items: List[CartItem] = []
item_counter: int = 0

@app.get("/api/cart")
async def list_cart():
    """Return all items currently in the cart."""
    return {"items": cart_items}

@app.post("/api/cart")
async def add_cart_item(item: CartItemRequest):
    """Add a new item to the cart.

    The incoming JSON body is validated against CartItemRequest. A new
    identifier is generated for the cart item to enable deletion later.
    """
    global item_counter
    item_counter += 1
    new_item = CartItem(item_id=item_counter, **item.dict())
    cart_items.append(new_item)
    return {"status": "added", "item": new_item}

@app.delete("/api/cart/{item_id}")
async def remove_cart_item(item_id: int):
    """Remove an item from the cart by its item_id."""
    global cart_items
    remaining = [i for i in cart_items if i.item_id != item_id]
    if len(remaining) == len(cart_items):
        raise HTTPException(status_code=404, detail="Item not found")
    cart_items = remaining
    return {"status": "deleted"}

@app.get("/healthz")
async def health() -> dict[str, str]:
    return {"status": "ok"}

