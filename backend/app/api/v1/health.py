import logging
from typing import Literal

import psycopg
from fastapi import APIRouter, Depends

from app.api.deps import get_app_settings
from app.core.config import Settings, to_psycopg_dsn
from app.modules.ai.llm import get_llm_circuit_breaker
from app.schemas.health import HealthResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


def _check_readonly_database(settings: Settings) -> Literal["connected", "unavailable"]:
    dsn = to_psycopg_dsn(settings.database_ro_url.get_secret_value())
    try:
        with psycopg.connect(dsn, connect_timeout=2) as conn, conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        return "connected"
    except (psycopg.Error, OSError):
        logger.warning("Read-only PostgreSQL health check failed.")
        return "unavailable"


@router.get("/health", response_model=HealthResponse)
def health_check(settings: Settings = Depends(get_app_settings)) -> HealthResponse:
    """Return service health and sanitized PostgreSQL/LLM configuration status."""
    db_status = _check_readonly_database(settings)
    overall_status: Literal["ok", "degraded"] = "ok" if db_status == "connected" else "degraded"
    cb = get_llm_circuit_breaker()
    return HealthResponse(
        status=overall_status,
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
        database_status=db_status,
        llm_provider=settings.llm_provider,
        llm_configured=settings.is_llm_configured,
        llm_providers_armed=settings.configured_llm_providers,
        llm_fallback_active=settings.is_multi_provider_resilient,
        llm_quarantined_providers=cb.get_quarantined_providers(),
    )
