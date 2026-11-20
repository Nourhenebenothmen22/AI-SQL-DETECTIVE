from typing import Literal

from pydantic import BaseModel, Field


class SchemaAnalysisOutput(BaseModel):
    """Structured output produced by Agent 1: Schema Analyst."""

    selected_tables: list[str] = Field(
        default_factory=list,
        description="Schema-qualified table names relevant to the question.",
    )
    relevant_columns: list[str] = Field(
        default_factory=list,
        description="Relevant table.column identifiers grounded in the introspected catalog.",
    )
    join_paths: list[str] = Field(
        default_factory=list,
        description="Explicit foreign-key join relationships required to answer the question.",
    )
    metric_definitions: list[str] = Field(
        default_factory=list,
        description="Clarified business metric formulas grounded in real columns.",
    )
    ambiguities: list[str] = Field(
        default_factory=list,
        description="Potential ambiguities or assumptions identified in the user request.",
    )
    needs_clarification: bool = Field(
        default=False,
        description="True only if the request cannot be mapped without clarification.",
    )
    query_intent: Literal[
        "aggregation",
        "filtering",
        "trend",
        "cohort",
        "anomaly",
        "comparison",
        "lookup",
        "general",
    ] = Field(
        default="general",
        description="AI-classified semantic intent of the user request.",
    )
    query_complexity: Literal["simple", "moderate", "complex"] = Field(
        default="moderate",
        description="AI-evaluated semantic query complexity.",
    )
    recommended_strategy: str = Field(
        default="",
        description="AI-recommended SQL strategy tailored to this intent and complexity.",
    )


class SQLGenerationOutput(BaseModel):
    """Structured output produced by Agent 2: SQL Generator."""

    sql: str = Field(
        min_length=1,
        description="Single PostgreSQL 16 read-only SELECT query with explicit column projections.",
    )
    rationale: str = Field(
        default="",
        description="Concise user-safe explanation of how the SQL answers the question.",
    )
    assumptions: list[str] = Field(
        default_factory=list,
        description="Explicit assumptions made (e.g., date range, status filter, ordering).",
    )


class QueryReviewOutput(BaseModel):
    """Structured output produced by Agent 3: Query Reviewer (quality/semantics only)."""

    status: Literal["approved", "needs_revision"] = Field(
        description="Semantic quality verdict (NOT a security authority).",
    )
    notes: list[str] = Field(
        default_factory=list,
        description="Concise semantic review observations (joins, grouping, NULLs, schema match).",
    )
    revision_feedback: str | None = Field(
        default=None,
        description="Actionable fix guidance if status is 'needs_revision'.",
    )


class ResultExplanationOutput(BaseModel):
    """Structured output produced by Agent 6: Result Explainer."""

    summary: str = Field(
        description="Concise plain-language answer grounded strictly in returned data.",
    )
    key_findings: list[str] = Field(
        default_factory=list,
        description="Bullet points referencing actual returned metrics and rows.",
    )
    caveats: list[str] = Field(
        default_factory=list,
        description="Data caveats, filters, truncation notes, or assumptions.",
    )
    suggested_chart: Literal["none", "bar", "line", "area", "donut", "horizontal_bar"] = Field(
        default="none",
        description="Best matching Recharts visualization type for this result set, or 'none'.",
    )


class OptimizationRecommendationItem(BaseModel):
    """Advisory PostgreSQL optimization recommendation produced by Agent 7."""

    severity: Literal["info", "warning", "high"] = "info"
    category: str = Field(description="indexing | scan | sorting | join | projection | rewrite")
    title: str
    detail: str
    suggestion: str
    suggested_sql_or_index: str | None = Field(
        default=None,
        description="Optional advisory DDL/SQL snippet (never auto-executed).",
    )


class OptimizationSynthesisOutput(BaseModel):
    """Structured output produced by Agent 7: Optimization Agent."""

    recommendations: list[OptimizationRecommendationItem] = Field(default_factory=list)
