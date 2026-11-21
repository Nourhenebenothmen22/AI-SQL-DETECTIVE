import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import case, create_engine, desc, func, insert, select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import Settings
from app.modules.ai.state import TokenLedgerRecord
from app.modules.database.models.app_meta import LLMTokenLedger
from app.modules.evallaps.types import (
    calculate_input_cost_usd,
    calculate_output_cost_usd,
    get_provider_renewal_meta,
)
from app.schemas.evallaps import (
    EvalLapsSummary,
    ModelBreakdownResponse,
    ModelExtremes,
    ModelUsageSummary,
    ProviderRenewalMetaSchema,
    ProviderUsageSummary,
    StageUsageSummary,
    TokenLedgerItem,
    TokenTimeSeriesPoint,
)

logger = logging.getLogger(__name__)

STAGE_DISPLAY_LABELS: dict[str, str] = {
    "schema_analyst": "Agent 1: Schema Analyst",
    "sql_generator": "Agent 2: SQL Generator",
    "query_reviewer": "Agent 3: Query Reviewer",
    "result_explainer": "Agent 6: Result Explainer",
    "optimization_agent": "Agent 7: Optimization Agent",
}


class EvalLapsRepository:
    """FinOps & LLMOps repository for PostgreSQL token ledger auditing and aggregations."""

    def __init__(self, settings: Settings, engine: Engine | None = None) -> None:
        self._settings = settings
        if engine is not None:
            self._engine = engine
        else:
            self._engine = create_engine(
                settings.database_app_url.get_secret_value(),
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=5,
            )

    def dispose(self) -> None:
        """Dispose of the underlying SQLAlchemy engine connection pool."""
        self._engine.dispose()

    def record_entries(self, run_id: UUID | None, entries: list[TokenLedgerRecord]) -> int:
        """Persist stage-level LLM token usage entries to app_meta.llm_token_ledger.

        Non-blocking to caller; catches SQLAlchemyError and logs warning safely.
        """
        if not entries:
            return 0

        rows: list[dict[str, Any]] = [
            {
                "id": uuid4(),
                "run_id": run_id,
                "stage_id": entry["stage_id"],
                "provider_name": entry["provider_name"].strip().lower(),
                "model_name": entry["model_name"],
                "key_fingerprint": entry["key_fingerprint"],
                "prompt_tokens": entry["prompt_tokens"],
                "completion_tokens": entry["completion_tokens"],
                "total_tokens": entry["total_tokens"],
                "estimated_savings_usd": entry["estimated_savings_usd"],
                "real_cost_usd": entry.get("real_cost_usd", 0.0),
                "http_status": entry.get("http_status", 200),
                "latency_ms": entry.get("latency_ms", 0.0),
            }
            for entry in entries
        ]

        stmt = insert(LLMTokenLedger.__table__).values(rows)
        try:
            with self._engine.begin() as conn:
                conn.execute(stmt)
            return len(rows)
        except (SQLAlchemyError, Exception):
            logger.warning("Failed to persist token ledger telemetry to app_meta.llm_token_ledger.")
            return 0

    def get_summary(self, window_days: int = 30) -> EvalLapsSummary:
        """Calculate global executive FinOps & LLMOps summary over the given rolling window."""
        now_utc = datetime.now(UTC)
        since_window = now_utc - timedelta(days=window_days)
        today_start = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = now_utc.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        t = LLMTokenLedger.__table__

        # 1. Rolling window aggregation
        window_stmt = select(
            func.coalesce(func.sum(t.c.total_tokens), 0).label("total_tokens"),
            func.coalesce(func.sum(t.c.prompt_tokens), 0).label("prompt_tokens"),
            func.coalesce(func.sum(t.c.completion_tokens), 0).label("completion_tokens"),
            func.coalesce(func.sum(t.c.estimated_savings_usd), 0.0).label("total_savings_usd"),
            func.coalesce(func.sum(t.c.real_cost_usd), 0.0).label("total_real_cost_usd"),
            func.count(t.c.id).label("total_calls"),
            func.count(func.distinct(t.c.provider_name)).label("providers_count"),
        ).where(t.c.recorded_at >= since_window)

        # 2. Today aggregation
        today_stmt = select(
            func.coalesce(func.sum(t.c.total_tokens), 0).label("today_tokens"),
            func.coalesce(func.sum(t.c.estimated_savings_usd), 0.0).label("today_savings_usd"),
        ).where(t.c.recorded_at >= today_start)

        # 3. This month aggregation
        month_stmt = select(
            func.coalesce(func.sum(t.c.total_tokens), 0).label("month_tokens"),
            func.coalesce(func.sum(t.c.estimated_savings_usd), 0.0).label("month_savings_usd"),
        ).where(t.c.recorded_at >= month_start)

        # 4. Top provider
        top_provider_stmt = (
            select(t.c.provider_name)
            .where(t.c.recorded_at >= since_window)
            .group_by(t.c.provider_name)
            .order_by(desc(func.sum(t.c.total_tokens)))
            .limit(1)
        )

        try:
            with self._engine.connect() as conn:
                w_row = conn.execute(window_stmt).one()
                t_row = conn.execute(today_stmt).one()
                m_row = conn.execute(month_stmt).one()
                top_p_val = conn.execute(top_provider_stmt).scalar_one_or_none()

            return EvalLapsSummary(
                total_tokens=int(w_row.total_tokens),
                prompt_tokens=int(w_row.prompt_tokens),
                completion_tokens=int(w_row.completion_tokens),
                total_savings_usd=round(float(w_row.total_savings_usd), 6),
                total_real_cost_usd=round(float(w_row.total_real_cost_usd), 6),
                total_calls=int(w_row.total_calls),
                today_tokens=int(t_row.today_tokens),
                today_savings_usd=round(float(t_row.today_savings_usd), 6),
                this_month_tokens=int(m_row.month_tokens),
                this_month_savings_usd=round(float(m_row.month_savings_usd), 6),
                providers_count=int(w_row.providers_count),
                top_provider=top_p_val,
            )
        except (SQLAlchemyError, Exception):
            logger.warning("Failed to aggregate EvalLaps summary.")
            return EvalLapsSummary()

    def get_provider_breakdown(self, window_days: int = 30) -> list[ProviderUsageSummary]:
        """Aggregate token usage and renewal characteristics by LLM provider."""
        since = datetime.now(UTC) - timedelta(days=window_days)
        t = LLMTokenLedger.__table__

        stmt = (
            select(
                t.c.provider_name,
                func.coalesce(func.sum(t.c.total_tokens), 0).label("total_tokens"),
                func.coalesce(func.sum(t.c.prompt_tokens), 0).label("prompt_tokens"),
                func.coalesce(func.sum(t.c.completion_tokens), 0).label("completion_tokens"),
                func.coalesce(func.sum(t.c.estimated_savings_usd), 0.0).label(
                    "estimated_savings_usd"
                ),
                func.coalesce(func.sum(t.c.real_cost_usd), 0.0).label("real_cost_usd"),
                func.count(t.c.id).label("total_calls"),
                func.coalesce(func.sum(case((t.c.http_status == 200, 1), else_=0)), 0).label(
                    "success_calls"
                ),
                func.coalesce(func.sum(case((t.c.http_status != 200, 1), else_=0)), 0).label(
                    "error_calls"
                ),
                func.coalesce(func.avg(t.c.latency_ms), 0.0).label("avg_latency_ms"),
            )
            .where(t.c.recorded_at >= since)
            .group_by(t.c.provider_name)
            .order_by(desc(func.sum(t.c.total_tokens)))
        )

        try:
            with self._engine.connect() as conn:
                rows = conn.execute(stmt).all()

            results: list[ProviderUsageSummary] = []
            for r in rows:
                p_name = str(r.provider_name)
                meta = get_provider_renewal_meta(p_name)
                renewal_schema = ProviderRenewalMetaSchema(
                    provider_name=meta.provider_name,
                    display_name=meta.display_name,
                    renewal_type=meta.renewal_type,
                    renewal_window_label=meta.renewal_window_label,
                    free_tier_limits_label=meta.free_tier_limits_label,
                    is_auto_renewable=meta.is_auto_renewable,
                    description=meta.description,
                )
                results.append(
                    ProviderUsageSummary(
                        provider_name=p_name,
                        total_tokens=int(r.total_tokens),
                        prompt_tokens=int(r.prompt_tokens),
                        completion_tokens=int(r.completion_tokens),
                        estimated_savings_usd=round(float(r.estimated_savings_usd), 6),
                        real_cost_usd=round(float(r.real_cost_usd), 6),
                        total_calls=int(r.total_calls),
                        success_calls=int(r.success_calls),
                        error_calls=int(r.error_calls),
                        avg_latency_ms=round(float(r.avg_latency_ms), 2),
                        renewal=renewal_schema,
                    )
                )
            return results
        except (SQLAlchemyError, Exception):
            logger.warning("Failed to aggregate EvalLaps provider breakdown.")
            return []

    def get_stage_breakdown(self, window_days: int = 30) -> list[StageUsageSummary]:
        """Aggregate token usage and savings by agent pipeline stage."""
        since = datetime.now(UTC) - timedelta(days=window_days)
        t = LLMTokenLedger.__table__

        stmt = (
            select(
                t.c.stage_id,
                func.coalesce(func.sum(t.c.total_tokens), 0).label("total_tokens"),
                func.coalesce(func.sum(t.c.prompt_tokens), 0).label("prompt_tokens"),
                func.coalesce(func.sum(t.c.completion_tokens), 0).label("completion_tokens"),
                func.coalesce(func.sum(t.c.estimated_savings_usd), 0.0).label(
                    "estimated_savings_usd"
                ),
                func.count(t.c.id).label("total_calls"),
                func.coalesce(func.avg(t.c.latency_ms), 0.0).label("avg_latency_ms"),
            )
            .where(t.c.recorded_at >= since)
            .group_by(t.c.stage_id)
            .order_by(desc(func.sum(t.c.total_tokens)))
        )

        try:
            with self._engine.connect() as conn:
                rows = conn.execute(stmt).all()

            return [
                StageUsageSummary(
                    stage_id=str(r.stage_id),
                    stage_label=STAGE_DISPLAY_LABELS.get(
                        str(r.stage_id), str(r.stage_id).replace("_", " ").title()
                    ),
                    total_tokens=int(r.total_tokens),
                    prompt_tokens=int(r.prompt_tokens),
                    completion_tokens=int(r.completion_tokens),
                    estimated_savings_usd=round(float(r.estimated_savings_usd), 6),
                    total_calls=int(r.total_calls),
                    avg_latency_ms=round(float(r.avg_latency_ms), 2),
                )
                for r in rows
            ]
        except (SQLAlchemyError, Exception):
            logger.warning("Failed to aggregate EvalLaps stage breakdown.")
            return []

    def get_run_ledger(self, run_id: UUID) -> list[TokenLedgerItem]:
        """Fetch all individual agent token consumption records for a specific query run."""
        t = LLMTokenLedger.__table__
        stmt = select(t).where(t.c.run_id == run_id).order_by(t.c.recorded_at.asc())

        try:
            with self._engine.connect() as conn:
                rows = conn.execute(stmt).all()

            return [
                TokenLedgerItem(
                    id=row.id,
                    run_id=row.run_id,
                    stage_id=row.stage_id,
                    provider_name=row.provider_name,
                    model_name=row.model_name,
                    key_fingerprint=row.key_fingerprint,
                    prompt_tokens=row.prompt_tokens,
                    completion_tokens=row.completion_tokens,
                    total_tokens=row.total_tokens,
                    estimated_savings_usd=float(row.estimated_savings_usd),
                    real_cost_usd=float(row.real_cost_usd),
                    http_status=row.http_status,
                    latency_ms=row.latency_ms,
                    recorded_at=row.recorded_at,
                )
                for row in rows
            ]
        except (SQLAlchemyError, Exception):
            logger.warning("Failed to retrieve token ledger for run_id %s.", run_id)
            return []

    def get_model_breakdown(self, window_days: int = 30) -> ModelBreakdownResponse:
        """Aggregate token usage, input/output cost split, and remaining quota by model."""
        now_utc = datetime.now(UTC)
        since_window = now_utc - timedelta(days=window_days)
        today_start = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
        t = LLMTokenLedger.__table__

        # 1. Rolling window query grouped by model_name and provider_name
        window_stmt = (
            select(
                t.c.model_name,
                t.c.provider_name,
                func.coalesce(func.sum(t.c.total_tokens), 0).label("total_tokens"),
                func.coalesce(func.sum(t.c.prompt_tokens), 0).label("prompt_tokens"),
                func.coalesce(func.sum(t.c.completion_tokens), 0).label("completion_tokens"),
                func.count(t.c.id).label("total_calls"),
                func.coalesce(func.sum(case((t.c.http_status == 200, 1), else_=0)), 0).label(
                    "success_calls"
                ),
                func.coalesce(func.sum(case((t.c.http_status != 200, 1), else_=0)), 0).label(
                    "error_calls"
                ),
                func.coalesce(func.avg(t.c.latency_ms), 0.0).label("avg_latency_ms"),
            )
            .where(t.c.recorded_at >= since_window)
            .group_by(t.c.model_name, t.c.provider_name)
            .order_by(desc(func.sum(t.c.total_tokens)))
        )

        # 2. Today tokens per model for remaining quota computation
        today_stmt = (
            select(
                t.c.model_name,
                func.coalesce(func.sum(t.c.total_tokens), 0).label("today_tokens"),
            )
            .where(t.c.recorded_at >= today_start)
            .group_by(t.c.model_name)
        )

        try:
            with self._engine.connect() as conn:
                w_rows = conn.execute(window_stmt).all()
                t_rows = conn.execute(today_stmt).all()
                today_map = {str(r.model_name): int(r.today_tokens) for r in t_rows}

            models: list[ModelUsageSummary] = []
            total_input_cost = 0.0
            total_output_cost = 0.0

            for r in w_rows:
                p_name = str(r.provider_name)
                m_name = str(r.model_name)
                prompt_t = int(r.prompt_tokens)
                comp_t = int(r.completion_tokens)
                tot_t = int(r.total_tokens)

                in_cost = calculate_input_cost_usd(prompt_t)
                out_cost = calculate_output_cost_usd(comp_t)
                tot_savings = round(in_cost + out_cost, 6)

                total_input_cost += in_cost
                total_output_cost += out_cost

                meta = get_provider_renewal_meta(p_name)
                daily_quota = meta.daily_token_quota
                today_used = today_map.get(m_name, 0)
                remaining = max(0, daily_quota - today_used)
                usage_pct = round((today_used / daily_quota) * 100.0, 1) if daily_quota > 0 else 0.0

                models.append(
                    ModelUsageSummary(
                        model_name=m_name,
                        provider_name=p_name,
                        display_name=meta.display_name,
                        total_tokens=tot_t,
                        prompt_tokens=prompt_t,
                        completion_tokens=comp_t,
                        input_cost_usd=in_cost,
                        output_cost_usd=out_cost,
                        total_savings_usd=tot_savings,
                        total_calls=int(r.total_calls),
                        success_calls=int(r.success_calls),
                        error_calls=int(r.error_calls),
                        avg_latency_ms=round(float(r.avg_latency_ms), 2),
                        estimated_daily_quota_tokens=daily_quota,
                        estimated_remaining_tokens=remaining,
                        usage_percentage=usage_pct,
                    )
                )

            # Mathematical identification of most and least used models without if-else
            most_used = max(models, key=lambda m: m.total_tokens) if models else None
            least_used = min(models, key=lambda m: m.total_tokens) if models else None

            return ModelBreakdownResponse(
                models=models,
                extremes=ModelExtremes(
                    most_used_model=most_used,
                    least_used_model=least_used,
                ),
                total_input_cost_usd=round(total_input_cost, 6),
                total_output_cost_usd=round(total_output_cost, 6),
                total_savings_usd=round(total_input_cost + total_output_cost, 6),
            )
        except (SQLAlchemyError, Exception):
            logger.warning("Failed to aggregate EvalLaps model breakdown.")
            return ModelBreakdownResponse(
                models=[],
                extremes=ModelExtremes(),
                total_input_cost_usd=0.0,
                total_output_cost_usd=0.0,
                total_savings_usd=0.0,
            )

    def get_today_token_usage_by_key(self) -> dict[str, int]:
        """Fetch today's total token consumption indexed by key_id for live load balancing."""
        today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        t = LLMTokenLedger.__table__
        stmt = (
            select(
                t.c.provider_name,
                t.c.key_fingerprint,
                func.coalesce(func.sum(t.c.total_tokens), 0).label("today_tokens"),
            )
            .where(t.c.recorded_at >= today_start)
            .group_by(t.c.provider_name, t.c.key_fingerprint)
        )
        try:
            with self._engine.connect() as conn:
                rows = conn.execute(stmt).all()
            return {f"{r.provider_name}:{r.key_fingerprint}": int(r.today_tokens) for r in rows}
        except (SQLAlchemyError, Exception):
            logger.warning("Failed to query today's key token usage.")
            return {}

    def get_token_timeseries(self, window_days: int = 30) -> list[TokenTimeSeriesPoint]:
        """Aggregate daily or hourly token burn rate from live PostgreSQL ledger."""
        now_utc = datetime.now(UTC)
        since = now_utc - timedelta(days=window_days)
        t = LLMTokenLedger.__table__

        trunc_unit = "hour" if window_days <= 1 else "day"
        bucket_col = func.date_trunc(trunc_unit, t.c.recorded_at).label("time_bucket")

        stmt = (
            select(
                bucket_col,
                func.coalesce(func.sum(t.c.prompt_tokens), 0).label("prompt_tokens"),
                func.coalesce(func.sum(t.c.completion_tokens), 0).label("completion_tokens"),
                func.coalesce(func.sum(t.c.total_tokens), 0).label("total_tokens"),
                func.coalesce(func.sum(t.c.estimated_savings_usd), 0.0).label("savings_usd"),
            )
            .where(t.c.recorded_at >= since)
            .group_by(bucket_col)
            .order_by(bucket_col.asc())
        )

        try:
            with self._engine.connect() as conn:
                rows = conn.execute(stmt).all()

            points: list[TokenTimeSeriesPoint] = []
            for r in rows:
                dt: datetime = r.time_bucket
                label = dt.strftime("%H:%M" if trunc_unit == "hour" else "%b %d")
                points.append(
                    TokenTimeSeriesPoint(
                        timestamp=dt,
                        label=label,
                        prompt_tokens=int(r.prompt_tokens),
                        completion_tokens=int(r.completion_tokens),
                        total_tokens=int(r.total_tokens),
                        savings_usd=round(float(r.savings_usd), 6),
                    )
                )
            return points
        except (SQLAlchemyError, Exception) as exc:
            logger.warning("Failed to fetch token timeseries: %s", exc)
            return []
