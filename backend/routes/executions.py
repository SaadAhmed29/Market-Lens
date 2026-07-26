from fastapi import APIRouter
from fastapi.responses import JSONResponse
import logging

from backend.modules.executions import get_all_executions, get_execution_detail

router = APIRouter(prefix="/api", tags=["executions"])
logger = logging.getLogger(__name__)

@router.get("/executions")
def list_executions():
    try:
        data = get_all_executions()
        return {"status": "success", "data": data}
    except Exception as e:
        logger.error(f"Error listing executions: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

@router.get("/executions/{strategy_name}")
def execution_detail(strategy_name: str):
    try:
        data = get_execution_detail(strategy_name)
        return {"status": "success", "data": data}
    except Exception as e:
        logger.error(f"Error fetching execution {strategy_name}: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})
