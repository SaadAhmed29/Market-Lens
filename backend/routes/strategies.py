"""
MarketLens — Strategies Router
Exposes endpoints for fetching strategy data.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.modules.strategies import get_all_strategies, get_strategy_detail

router = APIRouter(prefix="/api", tags=["strategies"])


@router.get("/strategies")
def strategies_list() -> JSONResponse:
    """Return a list of all strategies with basic stats."""
    try:
        data = get_all_strategies()
        return JSONResponse(content={"status": "success", "data": data})
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(exc)},
        )


@router.get("/strategies/{strategy_name}")
def strategy_detail(strategy_name: str) -> JSONResponse:
    """Return detailed information for a specific strategy."""
    try:
        data = get_strategy_detail(strategy_name)
        return JSONResponse(content={"status": "success", "data": data})
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(exc)},
        )
