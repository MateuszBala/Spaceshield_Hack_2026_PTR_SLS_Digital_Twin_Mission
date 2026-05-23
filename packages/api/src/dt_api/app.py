"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import router

app = FastAPI(
    title="Rocket Digital Twin API",
    version="0.1.0",
    description=(
        "Cyfrowy bliźniak rakiety: symulacja lotu, analiza orbity, "
        "opcjonalna optymalizacja masy startowej (AI)."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
