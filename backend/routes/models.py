from fastapi import APIRouter
from fastapi.responses import JSONResponse
from backend.modules.models import get_all_models, get_model_detail

router = APIRouter(prefix="/api", tags=["models"])

@router.get("/models")
def api_get_all_models():
    try:
        data = get_all_models()
        return {"status": "success", "data": data}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@router.get("/models/{model_name}")
def api_get_model_detail(model_name: str):
    try:
        data = get_model_detail(model_name)
        return {"status": "success", "data": data}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )
