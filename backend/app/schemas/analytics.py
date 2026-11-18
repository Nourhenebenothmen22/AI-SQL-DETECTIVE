from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class QueryRunHistoryItem(BaseModel):
    """Summary record for one historical query run."""

    id: UUID
    connection_id: str
    actor_id: str
    mode: Literal["nl", "manual_sql"]
    natural_language_prompt: str | None = None
    generated_sql: str | None = None
    validated_sql: str | None = None
    security_status: Literal["passed", "blocked"]
    review_status: str | None = None
    execution_status: Literal["success", "error", "timeout", "skipped", "cancelled"]
    execution_time_ms: float | None = None
    row_count: int | None = None
    was_truncated: bool = False
    optimization_count: int = 0
    created_at: datetime


class QueryRunHistoryDetail(QueryRunHistoryItem):
    """Full historical query run payload for reloading into the Workbench."""

    security_violations: list[str] = Field(default_factory=list)
    explain_plan: list[dict[str, Any]] | dict[str, Any] | None = None
    explanation_text: str | None = None
    optimizations: list[dict[str, Any]] = Field(default_factory=list)


class QueryRunHistoryResponse(BaseModel):
    """Paginated query run history response."""

    total: int
    limit: int
    offset: int
    items: list[QueryRunHistoryItem]


class AnalyticsSummary(BaseModel):
    total_runs: int
    passed_runs: int
    blocked_runs: int
    failed_runs: int
    cancelled_runs: int
    optimized_runs: int
    avg_execution_time_ms: float | None = None
    p95_execution_time_ms: float | None = None


class ExecutionTrendPoint(BaseModel):
    """Line chart point: execution latency trend over time."""

    date: str
    avg_execution_time_ms: float
    max_execution_time_ms: float
    run_count: int


class QueryComparisonItem(BaseModel):
    """Bar chart item: recent executed queries compared by latency and rows."""

    run_id: UUID
    label: str
    mode: Literal["nl", "manual_sql"]
    execution_time_ms: float
    row_count: int


class StatusDistributionItem(BaseModel):
    """Donut chart slice: query status breakdown."""

    status: Literal["passed", "blocked", "failed", "optimized"]
    count: int


class ActivityBucket(BaseModel):
    """Area chart point: daily query volume split by mode."""

    date: str
    total: int
    nl_count: int
    manual_sql_count: int


class DatabaseTableStat(BaseModel):
    """Horizontal bar item: PostgreSQL catalog statistics per table."""

    table_name: str
    schema_name: str
    estimated_row_count: int
    total_size_bytes: int
    index_count: int


class AnalyticsDashboardResponse(BaseModel):
    """Aggregated telemetry and database statistics powering all 5 Recharts views."""

    connection_id: str
    window_days: int
    summary: AnalyticsSummary
    execution_trends: list[ExecutionTrendPoint] = Field(default_factory=list)
    query_comparisons: list[QueryComparisonItem] = Field(default_factory=list)
    status_distribution: list[StatusDistributionItem] = Field(default_factory=list)
    activity_over_time: list[ActivityBucket] = Field(default_factory=list)
    database_statistics: list[DatabaseTableStat] = Field(default_factory=list)
