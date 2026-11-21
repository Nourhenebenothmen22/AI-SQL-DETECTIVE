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
    LoadBalancerDistribution,
    ModelBreakdownResponse,
    ProviderRenewalMetaSchema,
    ProviderShare,
    ProviderUsageSummary,
    QuarantinedKeyDetail,
    QuotaOverviewResponse,
    ResetCycleResponse,
    StageUsageSummary,
    TokenLedgerItem,
    TokenTimeSeriesResponse,
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

    def get_model_breakdown(self, window_days: int = 30) -> ModelBreakdownResponse:
        """Retrieve token consumption, input/output cost split, and remaining quota by model."""
        return self._repo.get_model_breakdown(window_days=window_days)

    def get_load_balancer_status(
        self, circuit_breaker: LLMCircuitBreaker | None = None
    ) -> LoadBalancerDistribution:
        """Calculate quota-aware load balancing state and determine next dispatched model."""
        cb = circuit_breaker or global_llm_circuit_breaker
        today_usage = self._repo.get_today_token_usage_by_key()
        cb_usage = cb.get_all_token_usage()

        chain_order = [
            p.strip().lower() for p in self._settings.llm_fallback_chain.split(",") if p.strip()
        ]
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

        shares: list[ProviderShare] = []
        total_tokens_all = 0
        healthy_keys: list[tuple[str, str, int]] = []

        for k_id, p_name in all_configured_keys:
            is_healthy = not cb.is_quarantined(k_id)
            meta = get_provider_renewal_meta(p_name)
            toks = max(today_usage.get(k_id, 0), cb_usage.get(k_id, 0))
            total_tokens_all += toks

            model_name = getattr(self._settings, f"{p_name}_model", p_name)
            tail = k_id.split(":", 1)[1] if ":" in k_id else "key"
            shares.append(
                ProviderShare(
                    provider_name=p_name,
                    display_name=meta.display_name,
                    model_name=str(model_name),
                    key_fingerprint=f"...{tail}",
                    today_tokens=toks,
                    traffic_share_percentage=0.0,
                    is_healthy=is_healthy,
                )
            )
            if is_healthy:
                healthy_keys.append((k_id, p_name, toks))

        if total_tokens_all > 0:
            for s in shares:
                s.traffic_share_percentage = round((s.today_tokens / total_tokens_all) * 100.0, 1)

        # Mathematical selection of next dispatched candidate without if-else:
        # minimum tokens consumed today among healthy keys
        if healthy_keys:
            next_k_id, next_p_name, _ = min(healthy_keys, key=lambda item: item[2])
            next_model = str(getattr(self._settings, f"{next_p_name}_model", next_p_name))
            next_tail = next_k_id.split(":", 1)[1] if ":" in next_k_id else "key"
        else:
            next_p_name = self._settings.llm_provider
            next_model = "default-model"
            next_tail = "none"

        return LoadBalancerDistribution(
            active_strategy="least_used_quota_aware",
            total_healthy_providers=len(healthy_keys),
            next_dispatched_model=next_model,
            next_dispatched_provider=next_p_name,
            dispatched_key_fingerprint=f"...{next_tail}",
            shares=shares,
        )

    def get_token_timeseries(self, window_days: int = 30) -> TokenTimeSeriesResponse:
        """Fetch daily/hourly token timeseries points from PostgreSQL."""
        points = self._repo.get_token_timeseries(window_days=window_days)
        total_tokens = sum(p.total_tokens for p in points)
        total_savings = round(sum(p.savings_usd for p in points), 6)
        return TokenTimeSeriesResponse(
            points=points,
            window_days=window_days,
            total_tokens=total_tokens,
            total_savings_usd=total_savings,
        )

    def get_quota_overview(
        self, circuit_breaker: LLMCircuitBreaker | None = None
    ) -> QuotaOverviewResponse:
        """Executive quota overview modeled after modern AI platforms (Google AI Studio)."""
        cb = circuit_breaker or global_llm_circuit_breaker
        summary = self._repo.get_summary(window_days=30)
        now_utc = datetime.now(UTC)

        # 1. Resets countdown computation
        next_daily_reset = (now_utc + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        seconds_until_daily = max(0, int((next_daily_reset - now_utc).total_seconds()))
        daily_pct_elapsed = round(((86400 - seconds_until_daily) / 86400) * 100.0, 1)

        next_month_y = now_utc.year + (1 if now_utc.month == 12 else 0)
        next_month_m = 1 if now_utc.month == 12 else now_utc.month + 1
        next_monthly_reset = datetime(next_month_y, next_month_m, 1, 0, 0, 0, tzinfo=UTC)
        seconds_until_monthly = max(0, int((next_monthly_reset - now_utc).total_seconds()))

        # 2. Configured and healthy keys count
        chain_order = [
            p.strip().lower() for p in self._settings.llm_fallback_chain.split(",") if p.strip()
        ]
        all_keys: list[str] = []
        for provider in chain_order:
            for key in self._settings.get_provider_keys(provider):
                raw = key.get_secret_value().strip()
                if raw:
                    tail = raw[-4:] if len(raw) >= 4 else "key"
                    all_keys.append(f"{provider}:{tail}")

        active_healthy = sum(1 for k in all_keys if not cb.is_quarantined(k))
        total_keys = len(all_keys)

        # 3. Quotas computation
        total_daily_quota = sum(get_provider_renewal_meta(p).daily_token_quota for p in chain_order)
        total_monthly_quota = total_daily_quota * 30

        today_toks = summary.today_tokens
        today_rem = max(0, total_daily_quota - today_toks)
        today_pct = (
            round((today_toks / total_daily_quota) * 100.0, 1) if total_daily_quota > 0 else 0.0
        )

        month_toks = summary.this_month_tokens
        month_rem = max(0, total_monthly_quota - month_toks)
        month_pct = (
            round((month_toks / total_monthly_quota) * 100.0, 1) if total_monthly_quota > 0 else 0.0
        )

        # Functional health status mapping without if-else
        health_thresholds = [
            (90.0, "critical"),
            (75.0, "warning"),
            (40.0, "moderate"),
            (0.0, "optimal"),
        ]
        pool_status = next(st for th, st in health_thresholds if today_pct >= th)

        return QuotaOverviewResponse(
            today_tokens=today_toks,
            today_quota_tokens=total_daily_quota,
            today_remaining_tokens=today_rem,
            today_usage_percentage=today_pct,
            month_tokens=month_toks,
            month_quota_tokens=total_monthly_quota,
            month_remaining_tokens=month_rem,
            month_usage_percentage=month_pct,
            seconds_until_daily_reset=seconds_until_daily,
            daily_reset_time_utc=next_daily_reset.strftime("%Y-%m-%dT%H:%M:%SZ"),
            seconds_until_monthly_reset=seconds_until_monthly,
            monthly_reset_date_utc=next_monthly_reset.strftime("%Y-%m-%d"),
            daily_cycle_percentage_elapsed=daily_pct_elapsed,
            active_healthy_keys=active_healthy,
            total_configured_keys=total_keys,
            pool_health_status=pool_status,
        )

    def reset_quota_cycle(
        self, circuit_breaker: LLMCircuitBreaker | None = None
    ) -> ResetCycleResponse:
        """Reset in-memory token counters and clear quarantines for cycle replenishment."""
        cb = circuit_breaker or global_llm_circuit_breaker
        cb.reset_all_tokens()
        return ResetCycleResponse(
            status="ok",
            message="Circuit breaker tokens and quarantines reset successfully.",
            reset_at=datetime.now(UTC),
        )
