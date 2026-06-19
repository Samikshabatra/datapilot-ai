"""FastAPI application entrypoint.

    uvicorn app.main:app --reload    (from the backend/ directory)
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import routes_ask, routes_eda, routes_upload

app = FastAPI(
    title="Autonomous Data Analyst Agent",
    version="0.1.0",
    description="Upload a dataset, ask in plain language. The agent writes code, "
    "runs it in a sandbox, self-corrects on errors, and shows its work.",
)

# Open CORS for the local Streamlit / React dev frontends. Tighten in deploy.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_upload.router)
app.include_router(routes_ask.router)
app.include_router(routes_eda.router)


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok"}
