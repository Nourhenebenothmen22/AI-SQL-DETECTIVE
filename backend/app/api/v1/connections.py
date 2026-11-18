from fastapi import APIRouter, Depends

from app.api.deps import get_connection_registry, get_current_context
from app.core.context import RequestContext
from app.modules.connections.registry import ConnectionRegistry
from app.schemas.connections import ConnectionListResponse

router = APIRouter(prefix="/connections", tags=["connections"])


@router.get("", response_model=ConnectionListResponse)
def list_connections(
    registry: ConnectionRegistry = Depends(get_connection_registry),
    _context: RequestContext = Depends(get_current_context),
) -> ConnectionListResponse:
    """Return preconfigured read-only database connections without exposing credentials."""
    return ConnectionListResponse(
        default_connection_id=registry.default_id,
        connections=registry.list_public(),
    )
