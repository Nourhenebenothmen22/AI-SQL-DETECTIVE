import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_context, get_evallaps_service
from app.core.context import RequestContext
from app.modules.evallaps import EvalLapsService
from app.schemas.evallaps import (
    EvalLapsSummary,
    ProviderRenewalMetaSchema,
    ProviderUsageSummary,
    StageUsageSummary,
    TokenLedgerItem,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/evallaps", tags=["evallaps"])


@router.get("/summary", response_model=EvalLapsSummary)
def get_evallaps_summary(
    window_days: int = Query(default=30, ge=1, le=365, description="Rolling window in days"),
    service: EvalLapsService = Depends(get_evallaps_service),
    _context: RequestContext = Depends(get_current_context),
) -> EvalLapsSummary:
    """Retrieve global FinOps savings, total tokens consumed, and call counts."""
    return service.get_observability_summary(window_days=window_days)


@router.get("/providers", response_model=list[ProviderUsageSummary])
def get_providers_usage(
    window_days: int = Query(default=30, ge=1, le=365, description="Rolling window in days"),
    service: EvalLapsService = Depends(get_evallaps_service),
    _context: RequestContext = Depends(get_current_context),
) -> list[ProviderUsageSummary]:
    """Retrieve token metrics, error rates, and renewal policy breakdown by provider."""
    return service.get_providers_status(window_days=window_days)


@router.get("/stages", response_model=list[StageUsageSummary])
def get_stages_usage(
    window_days: int = Query(default=30, ge=1, le=365, description="Rolling window in days"),
    service: EvalLapsService = Depends(get_evallaps_service),
    _context: RequestContext = Depends(get_current_context),
) -> list[StageUsageSummary]:
    """Retrieve token consumption and FinOps savings per agent stage."""
    return service.get_stages_breakdown(window_days=window_days)


@router.get("/runs/{run_id}", response_model=list[TokenLedgerItem])
def get_run_token_ledger(
    run_id: UUID,
    service: EvalLapsService = Depends(get_evallaps_service),
    _context: RequestContext = Depends(get_current_context),
) -> list[TokenLedgerItem]:
    """Retrieve granular stage-by-stage token ledger records for a specific query run."""
    return service.get_run_tokens(run_id=run_id)


@router.get("/renewals", response_model=list[ProviderRenewalMetaSchema])
def get_provider_renewal_catalog(
    service: EvalLapsService = Depends(get_evallaps_service),
    _context: RequestContext = Depends(get_current_context),
) -> list[ProviderRenewalMetaSchema]:
    """Retrieve quota reset windows and renewal characteristics for all free-tier providers."""
    return service.get_renewal_diagnostics()
