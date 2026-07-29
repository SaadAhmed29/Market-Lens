from fastapi import APIRouter, BackgroundTasks, HTTPException, Body
from typing import Any, Dict
from backend.modules.strategy_builder import (
    get_all_requests,
    get_strategy_options,
    get_request_detail,
    submit_backtest,
    save_strategy,
    preview_strategy_name,
)

router = APIRouter(prefix="/api", tags=["strategy-builder"])


@router.get("/strategy-builder/options")
def get_strategy_builder_options_route():
    """Return available strategies (from playbook) and saved ML models."""
    try:
        data = get_strategy_options()
        return {"status": "success", "data": data}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/strategy-builder")
def get_strategy_builder_requests_route():
    """List all strategy builder backtest requests."""
    try:
        data = get_all_requests()
        return {"status": "success", "data": data}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/strategy-builder/{request_id}")
def get_strategy_builder_detail_route(request_id: str):
    """Get detail for a single strategy builder backtest request."""
    try:
        data = get_request_detail(request_id)
        if data is None:
            return {"status": "error", "message": "Strategy builder request not found"}
        return {"status": "success", "data": data}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/strategy-builder")
def submit_strategy_builder_route(
    background_tasks: BackgroundTasks,
    config: Dict[str, Any] = Body(...),
):
    """Submit a strategy builder backtest as a background task."""
    try:
        req_id = submit_backtest(config, background_tasks)
        return {"status": "success", "data": {"request_id": req_id, "status": "Pending"}}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/strategy-builder/save")
def save_strategy_route(config: Dict[str, Any] = Body(...)):
    """Save a strategy to meta_data.strategies."""
    try:
        result = save_strategy(config)
        if "error" in result:
            return {"status": "error", "message": result["error"]}
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


from fastapi import Query

@router.get("/strategy-builder/preview-name")
def preview_name_route(
    mode: str = Query(""),
    exchange: str = Query(""),
    symbol: str = Query(""),
    timehorizon: str = Query(""),
    strategies: str = Query(""),
    models: str = Query(""),
):
    """Preview auto-generated strategy name."""
    try:
        strat_list = [s.strip() for s in strategies.split(",")] if strategies else []
        mod_list = [m.strip() for m in models.split(",")] if models else []
        
        name = preview_strategy_name(mode, exchange, symbol, timehorizon, strat_list, mod_list)
        return {"status": "success", "data": {"name": name}}
    except Exception as e:
        return {"status": "error", "message": str(e)}
