import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from uuid import UUID, uuid4

from sqlalchemy import create_engine, desc, func, insert, or_, select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import Settings
from app.modules.database.models.app_meta import QueryRun
from app.schemas.analytics import (
    ActivityBucket,
    AnalyticsSummary,
    ExecutionTrendPoint,
    QueryComparisonItem,
    QueryRunHistoryDetail,
    QueryRunHistoryItem,
    StatusDistributionItem,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class QueryRunRecordInput:
    """Typed telemetry record written to app_meta.query_runs."""

    connection_id: str
    actor_id: str
    mode: Literal["nl", "manual_sql"]
    security_status: Literal["passed", "blocked"]
    execution_status: Literal["success", "error", "timeout", "skipped", "cancelled"]
    natural_language_prompt: str | None = None
    generated_sql: str | None = None
    validated_sql: str | None = None
    security_violations: list[str] | None = None
    review_status: str | None = None
    execution_time_ms: float | None = None
    row_count: int | None = None
    was_truncated: bool = False
    explain_plan: list[dict[str, Any]] | dict[str, Any] | None = None
    explanation_text: str | None = None
    optimizations: list[dict[str, Any]] | None = None
    langsmith_run_id: str | None = None


def _row_to_history_item(row: Any) -> QueryRunHistoryItem:
    opt_list = row.optimizations_json if isinstance(row.optimizations_json, list) else []
    return QueryRunHistoryItem(
        id=row.id,
        connection_id=row.connection_id,
        actor_id=row.actor_id,
        mode=row.mode,
        natural_language_prompt=row.natural_language_prompt,
        generated_sql=row.generated_sql,
        validated_sql=row.validated_sql,
        security_status=row.security_status,
        review_status=row.review_status,
        execution_status=row.execution_status,
        execution_time_ms=row.execution_time_ms,
        row_count=row.row_count,
        was_truncated=bool(row.was_truncated),
        optimization_count=len(opt_list),
        created_at=row.created_at,
    )


def _row_to_history_detail(row: Any) -> QueryRunHistoryDetail:
    item = _row_to_history_item(row)
    violations = (
        row.security_violations_json if isinstance(row.security_violations_json, list) else []
    )
    optimizations = row.optimizations_json if isinstance(row.optimizations_json, list) else []
    return QueryRunHistoryDetail(
        **item.model_dump(),
        security_violations=violations,
        explain_plan=row.explain_plan_json,
        explanation_text=row.explanation_text,
        optimizations=optimizations,
    )


def _percentile(sorted_values: list[float], pct: float) -> float | None:
    if not sorted_values:
        return None
    idx = min(len(sorted_values) - 1, max(0, round((pct / 100.0) * (len(sorted_values) - 1))))
    return round(sorted_values[idx], 2)


class QueryRunRepository:
    """Records and reads query telemetry via the least-privilege app_meta role."""

    def __init__(self, settings: Settings) -> None:
        self._engine: Engine = create_engine(
            settings.database_app_url.get_secret_value(),
            pool_pre_ping=True,
            future=True,
        )

    def record_run(self, record: QueryRunRecordInput) -> UUID | None:
        """Persist a query run in app_meta.query_runs.

        Returns the generated UUID on success, or None if telemetry storage is
        temporarily unavailable (non-fatal to read-only query responses).
        """
        run_id = uuid4()
        stmt = insert(QueryRun.__table__).values(
            id=run_id,
            connection_id=record.connection_id,
            actor_id=record.actor_id,
            mode=record.mode,
            natural_language_prompt=record.natural_language_prompt,
            generated_sql=record.generated_sql,
            validated_sql=record.validated_sql,
            security_status=record.security_status,
            security_violations_json=record.security_violations,
            review_status=record.review_status,
            execution_status=record.execution_status,
            execution_time_ms=record.execution_time_ms,
            row_count=record.row_count,
            was_truncated=record.was_truncated,
            explain_plan_json=record.explain_plan,
            explanation_text=record.explanation_text,
            optimizations_json=record.optimizations,
            langsmith_run_id=record.langsmith_run_id,
        )
        try:
            with self._engine.begin() as conn:
                conn.execute(stmt)
            return run_id
        except SQLAlchemyError:
            logger.warning("Failed to persist query run telemetry to app_meta.query_runs.")
            return None

    def list_runs(
        self,
        *,
        connection_id: str | None = None,
        mode: str | None = None,
        security_status: str | None = None,
        execution_status: str | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[int, list[QueryRunHistoryItem]]:
        """List paginated query runs ordered newest-first."""
        table = QueryRun.__table__
        filters = []
        if connection_id:
            filters.append(table.c.connection_id == connection_id)
        if mode:
            filters.append(table.c.mode == mode)
        if security_status:
            filters.append(table.c.security_status == security_status)
        if execution_status:
            filters.append(table.c.execution_status == execution_status)
        if search and search.strip():
            pattern = f"%{search.strip()}%"
            filters.append(
                or_(
                    table.c.natural_language_prompt.ilike(pattern),
                    table.c.generated_sql.ilike(pattern),
                    table.c.validated_sql.ilike(pattern),
                )
            )

        count_stmt = select(func.count()).select_from(table).where(*filters)
        items_stmt = (
            select(table)
            .where(*filters)
            .order_by(desc(table.c.created_at))
            .limit(limit)
            .offset(offset)
        )

        with self._engine.connect() as conn:
            total = int(conn.execute(count_stmt).scalar_one())
            rows = conn.execute(items_stmt).fetchall()

        return total, [_row_to_history_item(row) for row in rows]

    def get_run(self, run_id: UUID) -> QueryRunHistoryDetail | None:
        """Retrieve a single query run by UUID."""
        table = QueryRun.__table__
        stmt = select(table).where(table.c.id == run_id)
        with self._engine.connect() as conn:
            row = conn.execute(stmt).fetchone()
        if row is None:
            return None
        return _row_to_history_detail(row)

    def get_analytics(
        self,
        *,
        connection_id: str,
        days: int = 14,
    ) -> tuple[
        AnalyticsSummary,
        list[ExecutionTrendPoint],
        list[QueryComparisonItem],
        list[StatusDistributionItem],
        list[ActivityBucket],
    ]:
        """Compute accurate telemetry aggregations from app_meta.query_runs."""
        table = QueryRun.__table__
        since = datetime.now(UTC) - timedelta(days=days)
        stmt = (
            select(table)
            .where(table.c.connection_id == connection_id, table.c.created_at >= since)
            .order_by(table.c.created_at.asc())
        )
        with self._engine.connect() as conn:
            rows = conn.execute(stmt).fetchall()

        total_runs = len(rows)
        passed_runs = 0
        blocked_runs = 0
        failed_runs = 0
        cancelled_runs = 0
        optimized_runs = 0
        latencies: list[float] = []

        trends_by_day: dict[str, list[float]] = {}
        activity_by_day: dict[str, dict[str, int]] = {}
        comparisons: list[QueryComparisonItem] = []

        for row in rows:
            day_key = row.created_at.astimezone(UTC).strftime("%Y-%m-%d")
            bucket = activity_by_day.setdefault(day_key, {"total": 0, "nl": 0, "manual_sql": 0})
            bucket["total"] += 1
            if row.mode == "nl":
                bucket["nl"] += 1
            else:
                bucket["manual_sql"] += 1

            has_opts = isinstance(row.optimizations_json, list) and len(row.optimizations_json) > 0
            if row.security_status == "blocked":
                blocked_runs += 1
            elif row.execution_status == "cancelled":
                cancelled_runs += 1
            elif row.execution_status in ("error", "timeout"):
                failed_runs += 1
            elif row.execution_status == "success":
                passed_runs += 1
                if has_opts:
                    optimized_runs += 1

            if row.execution_time_ms is not None and row.execution_status == "success":
                ms = float(row.execution_time_ms)
                latencies.append(ms)
                trends_by_day.setdefault(day_key, []).append(ms)

        # Build up to 8 most recent successful runs for bar-chart comparison.
        for row in reversed(rows):
            if row.execution_status != "success" or row.execution_time_ms is None:
                continue
            raw_label = (
                row.natural_language_prompt or row.validated_sql or row.generated_sql or "Query"
            ).strip()
            compact_label = " ".join(raw_label.split())
            if len(compact_label) > 42:
                compact_label = f"{compact_label[:39]}..."
            comparisons.append(
                QueryComparisonItem(
                    run_id=row.id,
                    label=compact_label,
                    mode=row.mode,
                    execution_time_ms=round(float(row.execution_time_ms), 2),
                    row_count=int(row.row_count or 0),
                )
            )
            if len(comparisons) >= 8:
                break
        comparisons.reverse()

        sorted_latencies = sorted(latencies)
        avg_ms = (
            round(sum(sorted_latencies) / len(sorted_latencies), 2) if sorted_latencies else None
        )
        p95_ms = _percentile(sorted_latencies, 95.0)

        summary = AnalyticsSummary(
            total_runs=total_runs,
            passed_runs=passed_runs,
            blocked_runs=blocked_runs,
            failed_runs=failed_runs,
            cancelled_runs=cancelled_runs,
            optimized_runs=optimized_runs,
            avg_execution_time_ms=avg_ms,
            p95_execution_time_ms=p95_ms,
        )

        execution_trends = [
            ExecutionTrendPoint(
                date=day,
                avg_execution_time_ms=round(sum(vals) / len(vals), 2),
                max_execution_time_ms=round(max(vals), 2),
                run_count=len(vals),
            )
            for day, vals in sorted(trends_by_day.items())
        ]

        # Non-overlapping status distribution for Donut chart:
        # 'optimized' = successful runs with optimization recommendations,
        # 'passed' = successful runs without recommendations,
        # 'blocked' = Security Gate rejections,
        # 'failed' = error, timeout, or cancelled runs.
        passed_clean = max(0, passed_runs - optimized_runs)
        status_distribution = [
            StatusDistributionItem(status="passed", count=passed_clean),
            StatusDistributionItem(status="optimized", count=optimized_runs),
            StatusDistributionItem(status="blocked", count=blocked_runs),
            StatusDistributionItem(status="failed", count=failed_runs + cancelled_runs),
        ]

        activity_over_time = [
            ActivityBucket(
                date=day,
                total=counts["total"],
                nl_count=counts["nl"],
                manual_sql_count=counts["manual_sql"],
            )
            for day, counts in sorted(activity_by_day.items())
        ]

        return summary, execution_trends, comparisons, status_distribution, activity_over_time

    def dispose(self) -> None:
        self._engine.dispose()
