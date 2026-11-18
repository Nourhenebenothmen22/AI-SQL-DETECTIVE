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
