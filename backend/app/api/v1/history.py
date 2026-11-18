import logging
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import SQLAlchemyError

from app.api.deps import get_current_context, get_query_run_repository
from app.core.context import RequestContext
from app.modules.history.repository import QueryRunRepository
from app.schemas.analytics import QueryRunHistoryDetail, QueryRunHistoryResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/history", tags=["history"])


@router.get("", response_model=QueryRunHistoryResponse)
def list_query_history(
    connection_id: str | None = Query(default=None),
    mode: Literal["nl", "manual_sql"] | None = Query(default=None),
    security_status: Literal["passed", "blocked"] | None = Query(default=None),
    execution_status: Literal["success", "error", "timeout", "skipped", "cancelled"] | None = Query(
        default=None
    ),
    search: str | None = Query(default=None, max_length=200),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    history_repo: QueryRunRepository = Depends(get_query_run_repository),
    _context: RequestContext = Depends(get_current_context),
) -> QueryRunHistoryResponse:
    """Return paginated auditable query-run history from app_meta.query_runs."""
    try:
        total, items = history_repo.list_runs(
            connection_id=connection_id,
            mode=mode,
            security_status=security_status,
            execution_status=execution_status,
            search=search,
            limit=limit,
            offset=offset,
        )
    except SQLAlchemyError:
        logger.warning("Failed to query app_meta.query_runs history.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Query history telemetry is temporarily unavailable.",
        ) from None

    return QueryRunHistoryResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=items,
    )


@router.get("/{run_id}", response_model=QueryRunHistoryDetail)
def get_query_history_detail(
    run_id: UUID,
    history_repo: QueryRunRepository = Depends(get_query_run_repository),
    _context: RequestContext = Depends(get_current_context),
) -> QueryRunHistoryDetail:
    """Return complete details for one historical query run."""
    try:
        detail = history_repo.get_run(run_id)
    except SQLAlchemyError:
        logger.warning("Failed to retrieve query run %s from app_meta.query_runs.", run_id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Query history telemetry is temporarily unavailable.",
        ) from None

    if detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Query run not found: {run_id}",
        )
    return detail
