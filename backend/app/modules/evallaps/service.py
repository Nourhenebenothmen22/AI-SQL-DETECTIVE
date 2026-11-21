import logging
from uuid import UUID

from app.core.config import Settings
from app.modules.ai.state import TokenLedgerRecord
from app.modules.evallaps.repository import EvalLapsRepository
from app.modules.evallaps.types import (
    PROVIDER_RENEWAL_REGISTRY,
)
from app.schemas.evallaps import (
    EvalLapsSummary,
    ProviderRenewalMetaSchema,
    ProviderUsageSummary,
    StageUsageSummary,
    TokenLedgerItem,
)

logger = logging.getLogger(__name__)


class EvalLapsService:
    """Core domain service for LLMOps token observability and FinOps savings tracking."""

    def __init__(self, repository: EvalLapsRepository, settings: Settings) -> None:
        self._repo = repository
        self._settings = settings

    def record_run_telemetry(self, run_id: UUID | None, entries: list[TokenLedgerRecord]) -> int:
        """Persist stage-level token ledger records generated during an AI workflow."""
        return self._repo.record_entries(run_id, entries)

    def get_observability_summary(self, window_days: int = 30) -> EvalLapsSummary:
        """Retrieve aggregated FinOps savings and token counts over a rolling window."""
        return self._repo.get_summary(window_days=window_days)

    def get_providers_status(self, window_days: int = 30) -> list[ProviderUsageSummary]:
        """Retrieve token consumption, error rates, and quota reset policies by provider."""
        return self._repo.get_provider_breakdown(window_days=window_days)

    def get_stages_breakdown(self, window_days: int = 30) -> list[StageUsageSummary]:
        """Retrieve consumption and savings broken down by multi-agent stage."""
        return self._repo.get_stage_breakdown(window_days=window_days)

    def get_run_tokens(self, run_id: UUID) -> list[TokenLedgerItem]:
        """Retrieve granular per-agent token telemetry for a single query run."""
        return self._repo.get_run_ledger(run_id=run_id)

    def get_renewal_diagnostics(self) -> list[ProviderRenewalMetaSchema]:
        """Return static renewal metadata catalog for all supported free-tier LLM providers."""
        return [
            ProviderRenewalMetaSchema(
                provider_name=meta.provider_name,
                display_name=meta.display_name,
                renewal_type=meta.renewal_type,
                renewal_window_label=meta.renewal_window_label,
                free_tier_limits_label=meta.free_tier_limits_label,
                is_auto_renewable=meta.is_auto_renewable,
                description=meta.description,
            )
            for meta in PROVIDER_RENEWAL_REGISTRY.values()
        ]
