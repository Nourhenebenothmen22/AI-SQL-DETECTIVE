from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class TokenLedgerItem(BaseModel):
    """Individual auditable token ledger telemetry row."""

    id: UUID
    run_id: UUID | None = None
    stage_id: str
    provider_name: str
    model_name: str
    key_fingerprint: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_savings_usd: float
    real_cost_usd: float = 0.0
    http_status: int = 200
    latency_ms: float = 0.0
    recorded_at: datetime


class ProviderRenewalMetaSchema(BaseModel):
    """Quota reset window and auto-renewal characteristics for an LLM provider."""

    provider_name: str
    display_name: str
    renewal_type: str
    renewal_window_label: str
    free_tier_limits_label: str
    is_auto_renewable: bool
    description: str


class ProviderUsageSummary(BaseModel):
    """Aggregated token consumption and quota diagnostics for a specific provider."""

    provider_name: str
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    estimated_savings_usd: float
    real_cost_usd: float = 0.0
    total_calls: int
    success_calls: int
    error_calls: int
    avg_latency_ms: float
    renewal: ProviderRenewalMetaSchema


class StageUsageSummary(BaseModel):
    """Aggregated token consumption breakdown across pipeline agent stages."""

    stage_id: str
    stage_label: str
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    estimated_savings_usd: float
    total_calls: int
    avg_latency_ms: float


class EvalLapsSummary(BaseModel):
    """Global LLMOps & FinOps executive summary for tokens, costs, and savings."""

    total_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_savings_usd: float = 0.0
    total_real_cost_usd: float = 0.0
    total_calls: int = 0
    today_tokens: int = 0
    today_savings_usd: float = 0.0
    this_month_tokens: int = 0
    this_month_savings_usd: float = 0.0
    providers_count: int = 0
    top_provider: str | None = None


class QuarantinedKeyDetail(BaseModel):
    """Diagnostic detail for an individual token temporarily in Circuit Breaker quarantine."""

    key_id: str
    provider_name: str
    display_name: str
    reason: str
    ttl_remaining_seconds: float
    renewal_type: str
    renewal_window_label: str
    is_auto_renewable: bool
    estimated_reset_seconds: int | None = None
    reset_target_label: str


class HealthyKeyDetail(BaseModel):
    """Detail for an active, non-quarantined API token in the multi-provider pool."""

    key_id: str
    provider_name: str
    display_name: str
    renewal_type: str


class CircuitBreakerStatusResponse(BaseModel):
    """Real-time diagnostic health and quarantine state of the multi-provider LLM pool."""

    quarantined: list[QuarantinedKeyDetail]
    healthy: list[HealthyKeyDetail]
    total_quarantined: int
    total_healthy: int
    all_healthy: bool
    active_primary_provider: str
    fallback_chain: list[str]
