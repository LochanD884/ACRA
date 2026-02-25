from fastapi import APIRouter, Depends

from app.api.v1.analyze import router as analyze_router
from app.api.v1.chat import router as chat_router
from app.api.v1.health import router as health_router
from app.core.security import require_api_key

api_router = APIRouter(dependencies=[Depends(require_api_key)])
api_router.include_router(health_router, tags=["health"])
api_router.include_router(analyze_router, tags=["analysis"])
api_router.include_router(chat_router, tags=["chat"])
