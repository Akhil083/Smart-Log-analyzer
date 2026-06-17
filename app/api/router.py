from fastapi import APIRouter

from app.api.v1.alert import router as alerts_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.logs import router as log_router

api_router = APIRouter()

api_router.include_router(log_router)
api_router.include_router(analytics_router)
api_router.include_router(alerts_router)
