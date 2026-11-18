from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class GoldenTestCase(BaseModel):
    """Canonical test case representing a curated business inquiry with gold SQL."""

    id: str = Field(..., description="Unique slug for the test case (e.g. golden_01).")
    question: str = Field(..., description="Natural language prompt.")
    category: str = Field(..., description="Query category: Joins, Aggregation, Filtering.")
    difficulty: Literal["easy", "medium", "hard"] = Field(..., description="Complexity tier.")
    golden_sql: str = Field(..., description="Canonical PostgreSQL 16 read-only query.")
    description: str = Field(..., description="Business rationale and tested logic.")


class EvalCaseResult(BaseModel):
    """Detailed score and comparison for an individual benchmark test case."""

    case_id: str
    question: str
    difficulty: Literal["easy", "medium", "hard"]
    category: str
    status: Literal["passed", "mismatch", "error", "blocked"]
    vast_passed: bool = Field(
        ...,
        description="Whether candidate SQL passed deterministic AST Security Gate.",
    )
    execution_accuracy: bool = Field(..., description="Whether returned data matches ground truth.")
    golden_sql: str
    generated_sql: str | None = None
    golden_row_count: int
    candidate_row_count: int | None = None
    latency_ms: float
    error_message: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class DifficultyMetric(BaseModel):
    total: int
    passed: int
    accuracy_percentage: float


class CategoryMetric(BaseModel):
    total: int
    passed: int
    accuracy_percentage: float


class EvalRunSummary(BaseModel):
    """Consolidated KPI report for a benchmark execution."""

    run_id: str
    model_name: str
    timestamp: datetime
    total_cases: int
    passed_cases: int
    vast_passed_count: int
    accuracy_percentage: float
    vast_percentage: float
    avg_latency_ms: float
    by_difficulty: dict[str, DifficultyMetric]
    by_category: dict[str, CategoryMetric]


class EvalRunResponse(BaseModel):
    """Full benchmark run payload including summary KPIs and case breakdowns."""

    summary: EvalRunSummary
    results: list[EvalCaseResult]


class EvalRunRequest(BaseModel):
    """Optional parameters when triggering a benchmark run."""

    case_ids: list[str] | None = None
    difficulty: Literal["easy", "medium", "hard"] | None = None
    mock_run: bool = Field(
        default=False,
        description="Run fast deterministic evaluation using golden queries for CI/demo.",
    )
