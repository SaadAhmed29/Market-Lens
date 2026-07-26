"""
MarketLens — Backend Entry Point
Run with:
    uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
or from the project root:
    python -m uvicorn backend.main:app --reload
"""

import sys
from pathlib import Path

# Ensure project root is on the path so sibling packages (utils, etc.) resolve.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes.dashboard import router as dashboard_router
from backend.routes.strategies import router as strategies_router
from backend.routes.models import router as models_router


# App

app = FastAPI(
    title="MarketLens API",
    description="Algorithmic trading platform — REST API",
    version="0.1.0",
)


# CORS — allow the Next.js dev server and any local origin during development

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",   # Next.js default dev port
        "http://localhost:3001",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers

app.include_router(dashboard_router)
app.include_router(strategies_router)
app.include_router(models_router)

# Health check


@app.get("/api/health", tags=["system"])
def health():
    return {"status": "ok"}
