from fastapi import APIRouter, BackgroundTasks, HTTPException, Body
from typing import Any, Dict
from backend.modules.backtest import (
    get_all_requests,
    get_strategy_options,
    get_request_detail,
    submit_backtest
)

router = APIRouter(prefix="/api", tags=["backtests"])

@router.get("/backtests")
def get_backtests_route():
    try:
        data = get_all_requests()
        return {"status": "success", "data": data}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/backtests/options")
def get_backtests_options_route():
    try:
        data = get_strategy_options()
        return {"status": "success", "data": data}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/backtests/{request_id}")
def get_backtest_detail_route(request_id: str):
    try:
        data = get_request_detail(request_id)
        if data is None:
            return {"status": "error", "message": "Backtest request not found"}
        return {"status": "success", "data": data}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/backtests")
def submit_backtest_route(background_tasks: BackgroundTasks, config: Dict[str, Any] = Body(...)):
    try:
        req_id = submit_backtest(config, background_tasks)
        return {"status": "success", "data": {"request_id": req_id, "status": "Pending"}}
    except Exception as e:
        return {"status": "error", "message": str(e)}
