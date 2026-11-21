import logging

import psycopg
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_connection_registry, get_current_context
from app.core.context import RequestContext
from app.modules.connections.registry import ConnectionRegistry
from app.modules.database.introspector import introspect_schema
from app.schemas.schema import SchemaIntrospectionResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/schema", tags=["schema"])


@router.get("", response_model=SchemaIntrospectionResponse)
def get_database_schema(
    connection_id: str | None = Query(
        default=None,
        description="Preconfigured read-only connection identifier.",
    ),
    refresh: bool = Query(
        default=False,
        description="Force refresh and bypass in-memory schema cache.",
    ),
    registry: ConnectionRegistry = Depends(get_connection_registry),
    _context: RequestContext = Depends(get_current_context),
) -> SchemaIntrospectionResponse:
    """Return introspected PostgreSQL catalog metadata for a configured read-only connection."""
    try:
        spec = registry.get(connection_id)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown connection_id: {connection_id!r}",
        ) from None

    try:
        if refresh:
            try:
                return introspect_schema(spec, force_refresh=True)
            except TypeError:
                return introspect_schema(spec)
        return introspect_schema(spec)
    except (psycopg.Error, OSError):
        logger.warning(
            "Schema introspection failed for connection_id=%s.",
            spec.id,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to introspect target database schema.",
        ) from None
