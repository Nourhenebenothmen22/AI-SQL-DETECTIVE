import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_scenario_service
from app.modules.scenarios.service import ScenarioGeneratorService
from app.schemas.scenarios import (
    ScenarioGenerateRequest,
    ScenarioGenerateResponse,
    ScenarioResetResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


@router.post(
    "/generate",
    response_model=ScenarioGenerateResponse,
    summary="Simulate a what-if scenario in the sandbox using AI",
)
async def generate_scenario(
    request: ScenarioGenerateRequest,
    scenario_service: ScenarioGeneratorService = Depends(get_scenario_service),
) -> ScenarioGenerateResponse:
    """Translate natural language scenario requests into relational synthetic data."""
    try:
        return await scenario_service.generate_scenario(request)
    except Exception as e:
        logger.error("Failed to generate scenario: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scenario generation failed: {e!s}",
        ) from None


@router.post(
    "/reset",
    response_model=ScenarioResetResponse,
    summary="Reset database to golden baseline seed",
)
def reset_database(
    scenario_service: ScenarioGeneratorService = Depends(get_scenario_service),
) -> ScenarioResetResponse:
    """Reset the sandbox database back to pristine golden baseline seed."""
    try:
        return scenario_service.reset_to_baseline()
    except Exception as e:
        logger.error("Failed to reset database: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database reset failed: {e!s}",
        ) from None
