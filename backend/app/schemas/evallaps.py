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


class ModelUsageSummary(BaseModel):
    """Detailed token consumption, input/output cost split, and remaining quota per model."""

    model_name: str
    provider_name: str
    display_name: str
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    input_cost_usd: float
    output_cost_usd: float
    total_savings_usd: float
    total_calls: int
    success_calls: int
    error_calls: int
    avg_latency_ms: float
    estimated_daily_quota_tokens: int
    estimated_remaining_tokens: int
    usage_percentage: float


class ModelExtremes(BaseModel):
    """Identification of most utilized and least utilized models for load balancing."""

    most_used_model: ModelUsageSummary | None = None
    least_used_model: ModelUsageSummary | None = None


class ModelBreakdownResponse(BaseModel):
    """Aggregated analytical payload broken down by individual model."""

    models: list[ModelUsageSummary]
    extremes: ModelExtremes
    total_input_cost_usd: float
    total_output_cost_usd: float
    total_savings_usd: float


class ProviderShare(BaseModel):
    """Distribution share of an individual provider key in the active load balancer."""

    provider_name: str
    display_name: str
    model_name: str
    key_fingerprint: str
    today_tokens: int
    traffic_share_percentage: float
    is_healthy: bool


class LoadBalancerDistribution(BaseModel):
    """Real-time load balancing and quota-aware distribution status across healthy keys."""

    active_strategy: str = "least_used_quota_aware"
    total_healthy_providers: int
    next_dispatched_model: str
    next_dispatched_provider: str
    dispatched_key_fingerprint: str
    shares: list[ProviderShare]


class TokenTimeSeriesPoint(BaseModel):
    """Single point in the token consumption time series."""

    timestamp: datetime
    label: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    savings_usd: float


class TokenTimeSeriesResponse(BaseModel):
    """Time-series aggregation of token consumption for charts."""

    points: list[TokenTimeSeriesPoint]
    window_days: int
    total_tokens: int
    total_savings_usd: float


class QuotaOverviewResponse(BaseModel):
    """Executive quota and token overview modeled after modern AI platforms."""

    today_tokens: int
    today_quota_tokens: int
    today_remaining_tokens: int
    today_usage_percentage: float
    month_tokens: int
    month_quota_tokens: int
    month_remaining_tokens: int
    month_usage_percentage: float
    seconds_until_daily_reset: int
    daily_reset_time_utc: str
    seconds_until_monthly_reset: int
    monthly_reset_date_utc: str
    daily_cycle_percentage_elapsed: float
    active_healthy_keys: int
    total_configured_keys: int
    pool_health_status: str


class ResetCycleResponse(BaseModel):
    """Response returned upon manual reset and resynchronization of the local quota cycle."""

    status: str
    message: str
    reset_at: datetime
