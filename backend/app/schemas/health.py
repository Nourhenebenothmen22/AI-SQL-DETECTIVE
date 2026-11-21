from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Sanitized health status for the backend and PostgreSQL connectivity."""

    status: Literal["ok", "degraded"]
    service: str
    version: str
    environment: str
    database_status: Literal["connected", "unavailable"]
    llm_provider: str
    llm_configured: bool
    llm_providers_armed: list[str] = []
    llm_tokens_armed: int = 0
    llm_fallback_active: bool = False
    llm_quarantined_providers: list[str] = []
