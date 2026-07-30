from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from backend.modules.wallets import get_all_wallets, get_wallet_detail, update_wallet_keys, get_unassigned_strategies, assign_strategy

router = APIRouter(prefix="/api", tags=["wallets"])

class KeysUpdate(BaseModel):
    api_key: str
    api_secret: str

@router.get("/wallets")
def get_wallets_list():
    try:
        data = get_all_wallets()
        return {"status": "success", "data": data}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

@router.get("/wallets/{account_name}")
def get_wallet(account_name: str):
    try:
        data = get_wallet_detail(account_name)
        return {"status": "success", "data": data}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

@router.put("/{account_name}/keys")
def update_keys(account_name: str, payload: KeysUpdate):
    try:
        result = update_wallet_keys(account_name, payload.api_key, payload.api_secret)
        if result.get("success"):
            return {"status": "success", "data": result}
        else:
            return JSONResponse(status_code=500, content={"status": "error", "message": result.get("message")})
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

class AssignStrategyPayload(BaseModel):
    strategy_name: str
    allow_execution: bool
    allow_simulation: bool

@router.get("/wallets/strategies/unassigned")
def get_unassigned():
    try:
        data = get_unassigned_strategies()
        return {"status": "success", "data": data}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

@router.put("/wallets/strategies/assign")
def assign_strategy_route(payload: AssignStrategyPayload):
    try:
        result = assign_strategy(payload.strategy_name, payload.allow_execution, payload.allow_simulation)
        if result.get("success"):
            return {"status": "success", "data": result}
        else:
            return JSONResponse(status_code=500, content={"status": "error", "message": result.get("message")})
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})
