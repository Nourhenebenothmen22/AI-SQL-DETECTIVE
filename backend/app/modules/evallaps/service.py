import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.core.config import Settings
from app.modules.ai.llm import LLMCircuitBreaker, global_llm_circuit_breaker
from app.modules.ai.state import TokenLedgerRecord
from app.modules.evallaps.repository import EvalLapsRepository
from app.modules.evallaps.types import (
    PROVIDER_RENEWAL_REGISTRY,
    get_provider_renewal_meta,
)
from app.schemas.evallaps import (
    CircuitBreakerStatusResponse,
    EvalLapsSummary,
    HealthyKeyDetail,
    ProviderRenewalMetaSchema,
    ProviderUsageSummary,
    QuarantinedKeyDetail,
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

    def get_circuit_breaker_status(
        self, circuit_breaker: LLMCircuitBreaker | None = None
    ) -> CircuitBreakerStatusResponse:
        """Inspect real-time health, quarantines, remaining TTLs, and quota reset times."""
        cb = circuit_breaker or global_llm_circuit_breaker
        quarantined_raw = cb.get_quarantine_details()
        quarantined_keys_set = {q["key_id"] for q in quarantined_raw}

        now_utc = datetime.now(UTC)
        chain_order = [
            p.strip().lower() for p in self._settings.llm_fallback_chain.split(",") if p.strip()
        ]

        # Collect all configured keys in priority chain order
        all_configured_keys: list[tuple[str, str]] = []
        for provider in chain_order:
            keys = self._settings.get_provider_keys(provider)
            for key in keys:
                raw = key.get_secret_value().strip()
                if not raw:
                    continue
                tail = raw[-4:] if len(raw) >= 4 else "key"
                key_id = f"{provider}:{tail}"
                all_configured_keys.append((key_id, provider))

        quarantined_details: list[QuarantinedKeyDetail] = []
        for q in quarantined_raw:
            k_id = q["key_id"]
            p_name = k_id.split(":", 1)[0] if ":" in k_id else k_id
            meta = get_provider_renewal_meta(p_name)
            ttl_rem = q["ttl_remaining_seconds"]

            # Compute quota reset target & estimated seconds
            reset_secs: int | None = None
            target_label = "Recharge manuelle requise"
            if meta.renewal_type == "sliding_window_1m":
                reset_secs = min(60, max(1, int(ttl_rem)))
                target_label = f"Fenêtre 60s (~{reset_secs}s)"
            elif meta.renewal_type == "rolling_daily_24h":
                midnight = (now_utc + timedelta(days=1)).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                reset_secs = int((midnight - now_utc).total_seconds())
                hours = reset_secs // 3600
                mins = (reset_secs % 3600) // 60
                target_label = f"00:00 UTC ({hours}h {mins}m)"
            elif meta.renewal_type == "monthly_credits":
                if now_utc.month == 12:
                    next_month = now_utc.replace(
                        year=now_utc.year + 1,
                        month=1,
                        day=1,
                        hour=0,
                        minute=0,
                        second=0,
                        microsecond=0,
                    )
                else:
                    next_month = now_utc.replace(
                        month=now_utc.month + 1,
                        day=1,
                        hour=0,
                        minute=0,
                        second=0,
                        microsecond=0,
                    )
                reset_secs = int((next_month - now_utc).total_seconds())
                days_left = reset_secs // 86400
                target_label = f"1er du mois (~{days_left}j)"

            quarantined_details.append(
                QuarantinedKeyDetail(
                    key_id=k_id,
                    provider_name=p_name,
                    display_name=meta.display_name,
                    reason=q["reason"],
                    ttl_remaining_seconds=ttl_rem,
                    renewal_type=meta.renewal_type,
                    renewal_window_label=meta.renewal_window_label,
                    is_auto_renewable=meta.is_auto_renewable,
                    estimated_reset_seconds=reset_secs,
                    reset_target_label=target_label,
                )
            )

        healthy_details: list[HealthyKeyDetail] = []
        for k_id, p_name in all_configured_keys:
            if k_id not in quarantined_keys_set and not cb.is_quarantined(k_id):
                meta = get_provider_renewal_meta(p_name)
                healthy_details.append(
                    HealthyKeyDetail(
                        key_id=k_id,
                        provider_name=p_name,
                        display_name=meta.display_name,
                        renewal_type=meta.renewal_type,
                    )
                )

        active_primary = (
            healthy_details[0].provider_name if healthy_details else self._settings.llm_provider
        )

        return CircuitBreakerStatusResponse(
            quarantined=quarantined_details,
            healthy=healthy_details,
            total_quarantined=len(quarantined_details),
            total_healthy=len(healthy_details),
            all_healthy=len(quarantined_details) == 0,
            active_primary_provider=active_primary,
            fallback_chain=chain_order,
        )
