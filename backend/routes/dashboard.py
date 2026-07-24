"""
MarketLens — Dashboard Router
Exposes GET /api/dashboard, which returns a single aggregated payload
covering all dashboard widgets.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.modules.dashboard import get_dashboard_data

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard")
def dashboard() -> JSONResponse:
    """
    Return all dashboard widget data in one response.

    Response shape::

        {
            "status": "success",
            "data": {
                "total_strategies": int,
                "active_strategies": int,
                "running_executions": int,
                "total_trades_executed": int,
                "running_simulations": int,
                "total_trades_simulated": int,
                "connected_accounts": int,
                "total_backtests": int,
                "total_return": float,
                "trained_ml_models": [{"name": str, "type": str}, ...],
                "strategies": [
                    {
                        "strategy_name": str,
                        "symbol": str,
                        "exchange": str,
                        "timehorizon": str,
                        "status": str,
                        "latest_return": float,
                        "sharpe_ratio": float,
                        "win_rate": float,
                    },
                    ...
                ]
            }
        }

    On failure returns HTTP 500 with::

        {"status": "error", "message": str}
    """
    try:
        data = get_dashboard_data()
        return JSONResponse(content={"status": "success", "data": data})
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(exc)},
        )
