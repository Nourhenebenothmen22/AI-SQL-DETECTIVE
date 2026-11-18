from fastapi import APIRouter

from app.api.v1.analytics import router as analytics_router
from app.api.v1.connections import router as connections_router
from app.api.v1.health import router as health_router
from app.api.v1.history import router as history_router
from app.api.v1.queries import router as queries_router
from app.api.v1.schema import router as schema_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(health_router)
api_v1_router.include_router(connections_router)
api_v1_router.include_router(schema_router)
api_v1_router.include_router(queries_router)
api_v1_router.include_router(history_router)
api_v1_router.include_router(analytics_router)
