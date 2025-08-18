"""Catalog Service

This microservice exposes a REST endpoint to return a catalogue of available RFID-enabled
business card templates. The catalogue is static for now but could easily be swapped
for a database-backed implementation in the future. The service uses FastAPI for
request handling and enables CORS to allow the browser-based frontend to
communicate with it during local development.

To run locally:

    uvicorn main:app --reload --host 0.0.0.0 --port 8001

In production, a Dockerfile can wrap this module and serve it via a WSGI/ASGI
server such as Uvicorn or Gunicorn with Uvicorn workers.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Catalog Service")

# Allow CORS from any origin during development. In production you should
# restrict this to the domain where your frontend is hosted.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static definition of card templates. Each template contains an ID, a human
# friendly name, a description and a colour code. The colour code will be
# leveraged by the frontend to style the preview card.

templates = [
    {
        "id": "classic-blue",
        "name": "Classic Blue",
        "description": "RFID-enabled card with campus ID encoding and classic university branding.",
        "color": "#1E90FF",
    },
    {
        "id": "modern-red",
        "name": "Modern Red",
        "description": "Minimal, modern layout. NFC chip supports quick contact & profile tap.",
        "color": "#FF4500",
    },
    {
        "id": "elegant-green",
        "name": "Elegant Green",
        "description": "Eco-forward design. Printed on recycled stock; RFID for secure lab access.",
        "color": "#2E8B57",
    },
    {
        "id": "sunshine-yellow",
        "name": "Sunshine Yellow",
        "description": "High-visibility theme. NFC links to personal profile & timetable.",
        "color": "#FFD700",
    },
    {
        "id": "royal-purple",
        "name": "Royal Purple",
        "description": "Premium finish for staff/faculty. RFID integrates with campus services.",
        "color": "#8A2BE2",
    },
]

@app.get("/api/catalog")
async def get_catalog():
    """Return the list of available card templates.

    The frontend fetches this endpoint to render the template selection view.
    """
    return {"templates": templates}
