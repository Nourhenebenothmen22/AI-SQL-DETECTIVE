from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import (
    get_connection_registry,
    get_current_context,
    get_eval_service,
)
from app.core.context import RequestContext
from app.modules.connections.registry import ConnectionRegistry
from app.modules.evals.service import EvalOpsService
from app.schemas.evals import (
    EvalRunRequest,
    EvalRunResponse,
    EvalRunSummary,
    GoldenTestCase,
)

router = APIRouter(prefix="/evals", tags=["evals"])


@router.get(
    "/cases",
    response_model=list[GoldenTestCase],
    summary="List golden benchmark test cases",
)
def list_golden_cases(
    difficulty: Annotated[str | None, Query(description="Filter by difficulty tier")] = None,
    eval_service: EvalOpsService = Depends(get_eval_service),
) -> list[GoldenTestCase]:
    """Retrieve the curated set of business golden test queries."""
    return eval_service.get_cases(difficulty)


@router.get(
    "/latest",
    response_model=EvalRunResponse,
    summary="Get the most recent benchmark evaluation run",
)
def get_latest_benchmark_run(
    eval_service: EvalOpsService = Depends(get_eval_service),
) -> EvalRunResponse:
    """Retrieve full results and accuracy metrics for the latest benchmark execution."""
    run = eval_service.get_latest_run()
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No benchmark run has been executed yet.",
        )
    return run


@router.get(
    "/history",
    response_model=list[EvalRunSummary],
    summary="List historical benchmark run summaries",
)
def get_benchmark_history(
    eval_service: EvalOpsService = Depends(get_eval_service),
) -> list[EvalRunSummary]:
    """Retrieve aggregated accuracy and latency trends over time."""
    return eval_service.get_history()


@router.post(
    "/run",
    response_model=EvalRunResponse,
    summary="Trigger an on-demand benchmark evaluation suite",
)
async def run_benchmark(
    payload: EvalRunRequest,
    eval_service: EvalOpsService = Depends(get_eval_service),
    connection_registry: ConnectionRegistry = Depends(get_connection_registry),
    context: RequestContext = Depends(get_current_context),
) -> EvalRunResponse:
    """Execute the golden queries against the LLM pipeline or mock baseline."""
    try:
        spec = connection_registry.get("ecommerce_demo")
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target database connection 'ecommerce_demo' is not configured.",
        )
    return await eval_service.run_benchmark(payload, spec, context)
