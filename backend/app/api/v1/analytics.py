import logging

import psycopg
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import SQLAlchemyError

from app.api.deps import (
    get_connection_registry,
    get_current_context,
    get_query_run_repository,
)
from app.core.context import RequestContext
from app.modules.connections.registry import ConnectionRegistry
from app.modules.database.introspector import introspect_schema
from app.modules.history.repository import QueryRunRepository
from app.schemas.analytics import AnalyticsDashboardResponse, DatabaseTableStat

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("", response_model=AnalyticsDashboardResponse)
def get_analytics_dashboard(
    connection_id: str | None = Query(default=None),
    days: int = Query(default=14, ge=1, le=90),
    registry: ConnectionRegistry = Depends(get_connection_registry),
    history_repo: QueryRunRepository = Depends(get_query_run_repository),
    _context: RequestContext = Depends(get_current_context),
) -> AnalyticsDashboardResponse:
    """Return telemetry metrics and PostgreSQL table statistics for Analytics charts."""
    try:
        spec = registry.get(connection_id)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown connection_id: {connection_id!r}",
        ) from None

    try:
        summary, trends, comparisons, status_dist, activity = history_repo.get_analytics(
            connection_id=spec.id,
            days=days,
        )
    except SQLAlchemyError:
        logger.warning("Failed to aggregate query analytics from app_meta.query_runs.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Query analytics telemetry is temporarily unavailable.",
        ) from None

    db_stats: list[DatabaseTableStat] = []
    try:
        schema = introspect_schema(spec)
        db_stats = sorted(
            [
                DatabaseTableStat(
                    table_name=t.table_name,
                    schema_name=t.schema_name,
                    estimated_row_count=t.estimated_row_count,
                    total_size_bytes=t.total_size_bytes,
                    index_count=len(t.indexes),
                )
                for t in schema.tables
            ],
            key=lambda item: item.estimated_row_count,
            reverse=True,
        )
    except (psycopg.Error, OSError):
        logger.warning("Unable to load target table statistics for connection_id=%s.", spec.id)

    return AnalyticsDashboardResponse(
        connection_id=spec.id,
        window_days=days,
        summary=summary,
        execution_trends=trends,
        query_comparisons=comparisons,
        status_distribution=status_dist,
        activity_over_time=activity,
        database_statistics=db_stats,
    )
