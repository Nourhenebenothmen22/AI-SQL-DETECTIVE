from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class SecurityCheckResponse(BaseModel):
    rule: str
    passed: bool
    detail: str


class ValidateSQLRequest(BaseModel):
    sql: str = Field(min_length=1, max_length=20_000)
    connection_id: str | None = None
    max_rows: int | None = Field(default=None, ge=1, le=5000)


class ValidateSQLResponse(BaseModel):
    connection_id: str
    security_status: Literal["passed", "blocked"]
    original_sql: str
    validated_sql: str | None = None
    enforced_limit: int | None = None
    limit_was_injected: bool = False
    limit_was_clamped: bool = False
    violations: list[str] = Field(default_factory=list)
    checks: list[SecurityCheckResponse] = Field(default_factory=list)


class ExecuteSQLRequest(BaseModel):
    sql: str = Field(min_length=1, max_length=20_000)
    connection_id: str | None = None
    max_rows: int | None = Field(default=None, ge=1, le=5000)
    include_explain: bool = True


class PlanFindingResponse(BaseModel):
    severity: str
    category: str
    title: str
    detail: str
    suggestion: str


class PlanSummaryResponse(BaseModel):
    root_node_type: str
    startup_cost: float
    total_cost: float
    estimated_rows: int
    plan_width: int
    node_types: list[str]
    has_sort: bool
    has_nested_loop: bool
    has_hash_join: bool
    findings: list[PlanFindingResponse]


class ExecuteSQLResponse(BaseModel):
    run_id: UUID | None = None
    connection_id: str
    original_sql: str
    validated_sql: str | None = None
    security_status: Literal["passed", "blocked"]
    security_violations: list[str] = Field(default_factory=list)
    security_checks: list[SecurityCheckResponse] = Field(default_factory=list)
    enforced_limit: int | None = None
    limit_was_injected: bool = False
    limit_was_clamped: bool = False
    execution_status: Literal["success", "error", "timeout", "skipped", "cancelled"]
    columns: list[str] = Field(default_factory=list)
    rows: list[dict[str, Any]] = Field(default_factory=list)
    row_count: int = 0
    was_truncated: bool = False
    execution_time_ms: float | None = None
    execution_error: str | None = None
    explain_plan: list[dict[str, Any]] | None = None
    plan_summary: PlanSummaryResponse | None = None
    warnings: list[str] = Field(default_factory=list)


class AskQueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    connection_id: str | None = None
    max_rows: int | None = Field(default=None, ge=1, le=5000)
    include_explain: bool = True


class StageStatusResponse(BaseModel):
    stage: str
    status: Literal["completed", "retrying", "blocked", "error", "skipped"]
    attempt: int
    duration_ms: float
    summary: str


class ExplanationResponse(BaseModel):
    summary: str
    key_findings: list[str] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)
    suggested_chart: Literal["none", "bar", "line", "area", "donut", "horizontal_bar"] = "none"


class OptimizationRecommendationResponse(BaseModel):
    severity: Literal["info", "warning", "high"] = "info"
    category: str
    title: str
    detail: str
    suggestion: str
    suggested_sql_or_index: str | None = None


class QueryClassificationResponse(BaseModel):
    intent: Literal[
        "aggregation",
        "filtering",
        "trend",
        "cohort",
        "anomaly",
        "comparison",
        "lookup",
        "general",
    ] = "general"
    complexity: Literal["simple", "moderate", "complex"] = "moderate"
    recommended_strategy: str = ""


class AskQueryResponse(BaseModel):
    run_id: UUID | None = None
    connection_id: str
    question: str
    classification: QueryClassificationResponse | None = None
    selected_tables: list[str] = Field(default_factory=list)
    ambiguities: list[str] = Field(default_factory=list)
    candidate_sql: str | None = None
    validated_sql: str | None = None
    generation_rationale: str | None = None
    assumptions: list[str] = Field(default_factory=list)
    review_status: Literal["approved", "needs_revision"] | None = None
    review_notes: list[str] = Field(default_factory=list)
    security_status: Literal["passed", "blocked"]
    security_violations: list[str] = Field(default_factory=list)
    security_checks: list[SecurityCheckResponse] = Field(default_factory=list)
    enforced_limit: int | None = None
    limit_was_injected: bool = False
    limit_was_clamped: bool = False
    execution_status: Literal["success", "error", "timeout", "skipped", "cancelled"]
    columns: list[str] = Field(default_factory=list)
    rows: list[dict[str, Any]] = Field(default_factory=list)
    row_count: int = 0
    was_truncated: bool = False
    execution_time_ms: float | None = None
    execution_error: str | None = None
    explanation: ExplanationResponse | None = None
    explain_plan: list[dict[str, Any]] | None = None
    plan_summary: PlanSummaryResponse | None = None
    optimization_status: Literal["completed", "partial", "skipped"] = "skipped"
    optimizations: list[OptimizationRecommendationResponse] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    stages: list[StageStatusResponse] = Field(default_factory=list)
