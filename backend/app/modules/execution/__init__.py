"""Read-only PostgreSQL query execution and deterministic EXPLAIN (FORMAT JSON) analysis."""

from app.modules.execution.executor import ExecutionResult, SQLExecutor
from app.modules.execution.plan_parser import PlanFinding, PlanSummary, analyze_explain_plan

__all__ = [
    "ExecutionResult",
    "PlanFinding",
    "PlanSummary",
    "SQLExecutor",
    "analyze_explain_plan",
]
