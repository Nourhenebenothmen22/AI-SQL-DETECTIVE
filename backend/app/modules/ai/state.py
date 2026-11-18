import operator
from typing import Annotated, Any, Literal, TypedDict

from app.modules.execution.plan_parser import PlanSummary
from app.modules.security.types import SecurityRuleCheck, ValidatedSQL

MAX_REVIEW_REVISIONS = 2
MAX_EXECUTION_RETRIES = 1


class StageRecord(TypedDict):
    """Safe, user-visible execution record for one pipeline stage."""

    stage: str
    status: Literal["completed", "retrying", "blocked", "error", "skipped"]
    attempt: int
    duration_ms: float
    summary: str


class DetectiveState(TypedDict, total=False):
    """Typed LangGraph shared state across all 7 AI SQL Detective agents."""

    # Request & introspected context
    connection_id: str
    user_question: str
    max_rows: int
    include_explain: bool
    schema_prompt: str
    allowed_schemas: list[str]

    # Agent 1: Schema Analyst
    selected_tables: list[str]
    relevant_columns: list[str]
    join_paths: list[str]
    metric_definitions: list[str]
    ambiguities: list[str]
    needs_clarification: bool

    # Agent 2: SQL Generator
    candidate_sql: str
    generation_rationale: str
    assumptions: list[str]

    # Agent 3: Query Reviewer (quality/semantics only — NOT security)
    review_status: Literal["approved", "needs_revision"]
    review_notes: list[str]
    revision_feedback: str | None
    revision_count: int

    # Agent 4: Independent Security Gate (100% deterministic SQLGlot AST)
    security_status: Literal["passed", "blocked"]
    security_violations: list[str]
    security_checks: list[SecurityRuleCheck]
    validated_sql_artifact: ValidatedSQL | None
    normalized_sql: str | None
    enforced_limit: int | None
    limit_was_injected: bool
    limit_was_clamped: bool

    # Agent 5: SQL Executor (100% deterministic read-only PostgreSQL)
    execution_status: Literal["success", "error", "timeout", "skipped", "cancelled"]
    columns: list[str]
    rows: list[dict[str, Any]]
    row_count: int
    was_truncated: bool
    execution_time_ms: float | None
    execution_error: str | None
    explain_plan: list[dict[str, Any]] | None
    plan_summary: PlanSummary | None
    execution_retry_count: int

    # Agent 6: Result Explainer
    explanation_summary: str | None
    key_findings: list[str]
    caveats: list[str]
    suggested_chart: Literal["none", "bar", "line", "area", "donut", "horizontal_bar"]

    # Agent 7: Optimization Agent (parallel non-blocking branch)
    optimization_status: Literal["completed", "partial", "skipped"]
    optimization_recommendations: list[dict[str, Any]]

    # Parallel-safe append-only logs
    warnings: Annotated[list[str], operator.add]
    stages: Annotated[list[StageRecord], operator.add]
