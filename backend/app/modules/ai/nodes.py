import asyncio
import json
import logging
import threading
import time
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any, TypeVar

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel

from app.modules.ai.prompts import (
    OPTIMIZATION_AGENT_SYSTEM_PROMPT,
    QUERY_REVIEWER_SYSTEM_PROMPT,
    RESULT_EXPLAINER_SYSTEM_PROMPT,
    SCHEMA_ANALYST_SYSTEM_PROMPT,
    SQL_GENERATOR_SYSTEM_PROMPT,
)
from app.modules.ai.schemas import (
    OptimizationRecommendationItem,
    OptimizationSynthesisOutput,
    QueryReviewOutput,
    ResultExplanationOutput,
    SchemaAnalysisOutput,
    SQLGenerationOutput,
)
from app.modules.ai.state import (
    MAX_EXECUTION_RETRIES,
    MAX_REVIEW_REVISIONS,
    DetectiveState,
    StageRecord,
)
from app.modules.connections.registry import DatabaseConnectionSpec
from app.modules.execution.executor import SQLExecutor
from app.modules.execution.plan_parser import PlanSummary
from app.modules.security.gate import SecurityGate

logger = logging.getLogger(__name__)

EventEmitter = Callable[[str, dict[str, Any]], Awaitable[None]]

PRIMARY_STAGE_LABELS: dict[str, str] = {
    "schema_analyst": "Schema Analyst",
    "sql_generator": "SQL Generator",
    "query_reviewer": "Query Reviewer",
    "security_gate": "Security Gate",
    "sql_executor": "SQL Executor",
    "result_explainer": "Result Explainer",
}


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


async def _emit(config: RunnableConfig | None, event: str, payload: dict[str, Any]) -> None:
    if not config:
        return
    emitter: EventEmitter | None = config.get("configurable", {}).get("event_emitter")
    if emitter is not None:
        await emitter(event, payload)


def _get_cancel_event(config: RunnableConfig | None) -> threading.Event | None:
    if not config:
        return None
    return config.get("configurable", {}).get("cancel_event")


TModel = TypeVar("TModel", bound=BaseModel)


async def _invoke_structured(
    llm: BaseChatModel,
    output_schema: type[TModel],
    system_prompt: str,
    user_prompt: str,
    *,
    timeout_seconds: float,
) -> TModel:
    runnable = llm.with_structured_output(output_schema)
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]
    result = await asyncio.wait_for(runnable.ainvoke(messages), timeout=timeout_seconds)
    if isinstance(result, output_schema):
        return result
    return output_schema.model_validate(result)


def _deterministic_findings_as_recommendations(
    plan_summary: PlanSummary | None,
) -> list[dict[str, Any]]:
    if plan_summary is None:
        return []
    return [
        OptimizationRecommendationItem(
            severity=(
                finding.severity if finding.severity in ("info", "warning", "high") else "info"
            ),
            category=finding.category,
            title=finding.title,
            detail=finding.detail,
            suggestion=finding.suggestion,
            suggested_sql_or_index=None,
        ).model_dump()
        for finding in plan_summary.findings
    ]


class DetectiveNodes:
    """Encapsulates all 7 LangGraph agent nodes with strict separation of concerns."""

    def __init__(
        self,
        *,
        llm: BaseChatModel,
        security_gate: SecurityGate,
        sql_executor: SQLExecutor,
        connection_spec: DatabaseConnectionSpec,
        hard_max_rows: int,
        lock_timeout_ms: int,
        llm_timeout_seconds: int,
        settings: Any = None,
        llm_factory: Callable[..., BaseChatModel] | None = None,
    ) -> None:
        self._llm = llm
        self._gate = security_gate
        self._executor = sql_executor
        self._spec = connection_spec
        self._hard_max_rows = hard_max_rows
        self._lock_timeout_ms = lock_timeout_ms
        self._llm_timeout_seconds = llm_timeout_seconds
        self._settings = settings
        self._llm_factory = llm_factory

    def _get_active_llm(self) -> BaseChatModel:
        """Dynamically resolve active LLM, prioritizing non-quarantined providers."""
        if self._settings is not None and self._llm_factory is not None:
            return self._llm_factory(self._settings)
        return self._llm

    async def schema_analyst(
        self,
        state: DetectiveState,
        config: RunnableConfig,
    ) -> dict[str, Any]:
        """Agent 1: Ground user question against introspected PostgreSQL catalog."""
        stage = "schema_analyst"
        start = time.perf_counter()
        await _emit(
            config,
            "stage_started",
            {
                "stage": stage,
                "label": PRIMARY_STAGE_LABELS[stage],
                "attempt": 1,
                "timestamp": _utc_now_iso(),
            },
        )

        prompt = (
            f"User question:\n{state['user_question']}\n\n"
            f"Introspected PostgreSQL catalog:\n{state['schema_prompt']}"
        )
        output = await _invoke_structured(
            self._get_active_llm(),
            SchemaAnalysisOutput,
            SCHEMA_ANALYST_SYSTEM_PROMPT,
            prompt,
            timeout_seconds=self._llm_timeout_seconds,
        )

        duration_ms = round((time.perf_counter() - start) * 1000.0, 2)
        tables_text = ", ".join(output.selected_tables[:5]) or "catalog analyzed"
        intent_label = output.query_intent.capitalize()
        complexity_label = output.query_complexity.capitalize()
        summary = (
            f"Selected {len(output.selected_tables)} table(s): {tables_text} · "
            f"Intent: {intent_label} · Complexity: {complexity_label}"
        )
        await _emit(
            config,
            "stage_completed",
            {
                "stage": stage,
                "label": PRIMARY_STAGE_LABELS[stage],
                "status": "completed",
                "attempt": 1,
                "duration_ms": duration_ms,
                "summary": summary,
            },
        )

        return {
            "selected_tables": output.selected_tables,
            "relevant_columns": output.relevant_columns,
            "join_paths": output.join_paths,
            "metric_definitions": output.metric_definitions,
            "ambiguities": output.ambiguities,
            "needs_clarification": output.needs_clarification,
            "query_intent": output.query_intent,
            "query_complexity": output.query_complexity,
            "recommended_strategy": output.recommended_strategy,
            "stages": [
                StageRecord(
                    stage=stage,
                    status="completed",
                    attempt=1,
                    duration_ms=duration_ms,
                    summary=summary,
                )
            ],
        }

    async def sql_generator(
        self,
        state: DetectiveState,
        config: RunnableConfig,
    ) -> dict[str, Any]:
        """Agent 2: Translate grounded schema context into PostgreSQL 16 SELECT SQL."""
        stage = "sql_generator"
        attempt = state.get("revision_count", 0) + state.get("execution_retry_count", 0) + 1
        start = time.perf_counter()
        await _emit(
            config,
            "stage_started",
            {
                "stage": stage,
                "label": PRIMARY_STAGE_LABELS[stage],
                "attempt": attempt,
                "timestamp": _utc_now_iso(),
            },
        )

        parts = [
            f"User question:\n{state['user_question']}",
            f"Query intent: {state.get('query_intent', 'general')}",
            f"Query complexity: {state.get('query_complexity', 'moderate')}",
        ]
        if state.get("recommended_strategy"):
            parts.append(f"Recommended generation strategy:\n{state['recommended_strategy']}")
        parts.extend(
            [
                f"Allowed schemas: {', '.join(state['allowed_schemas'])}",
                f"Selected tables: {', '.join(state.get('selected_tables', []))}",
                f"Relevant columns: {', '.join(state.get('relevant_columns', []))}",
                f"Join paths: {'; '.join(state.get('join_paths', []))}",
                f"Metric definitions: {'; '.join(state.get('metric_definitions', []))}",
                f"Full introspected catalog:\n{state['schema_prompt']}",
            ]
        )
        if state.get("revision_feedback"):
            parts.append(f"Query Reviewer revision feedback:\n{state['revision_feedback']}")
        if state.get("execution_error"):
            parts.append(
                f"Previous SQL failed with PostgreSQL error:\n{state['execution_error']}\n"
                f"Previous SQL:\n{state.get('candidate_sql', '')}"
            )

        output = await _invoke_structured(
            self._get_active_llm(),
            SQLGenerationOutput,
            SQL_GENERATOR_SYSTEM_PROMPT,
            "\n\n".join(parts),
            timeout_seconds=self._llm_timeout_seconds,
        )

        duration_ms = round((time.perf_counter() - start) * 1000.0, 2)
        summary = (
            f"Generated candidate SQL (attempt {attempt})"
            if attempt > 1
            else "Generated candidate PostgreSQL SELECT query"
        )
        await _emit(
            config,
            "stage_completed",
            {
                "stage": stage,
                "label": PRIMARY_STAGE_LABELS[stage],
                "status": "completed",
                "attempt": attempt,
                "duration_ms": duration_ms,
                "summary": summary,
            },
        )

        return {
            "candidate_sql": output.sql.strip(),
            "generation_rationale": output.rationale.strip(),
            "assumptions": output.assumptions,
            "revision_feedback": None,
            "execution_error": None,
            "stages": [
                StageRecord(
                    stage=stage,
                    status="completed",
                    attempt=attempt,
                    duration_ms=duration_ms,
                    summary=summary,
                )
            ],
        }

    async def query_reviewer(
        self,
        state: DetectiveState,
        config: RunnableConfig,
    ) -> dict[str, Any]:
        """Agent 3: Semantic & logical SQL review (quality ONLY, never security)."""
        stage = "query_reviewer"
        current_revisions = state.get("revision_count", 0)
        attempt = current_revisions + state.get("execution_retry_count", 0) + 1
        start = time.perf_counter()
        await _emit(
            config,
            "stage_started",
            {
                "stage": stage,
                "label": PRIMARY_STAGE_LABELS[stage],
                "attempt": attempt,
                "timestamp": _utc_now_iso(),
            },
        )

        prompt = (
            f"User question:\n{state['user_question']}\n\n"
            f"Candidate SQL:\n{state.get('candidate_sql', '')}\n\n"
            f"Introspected PostgreSQL catalog:\n{state['schema_prompt']}"
        )
        output = await _invoke_structured(
            self._get_active_llm(),
            QueryReviewOutput,
            QUERY_REVIEWER_SYSTEM_PROMPT,
            prompt,
            timeout_seconds=self._llm_timeout_seconds,
        )

        duration_ms = round((time.perf_counter() - start) * 1000.0, 2)
        will_retry = output.status == "needs_revision" and current_revisions < MAX_REVIEW_REVISIONS
        next_revision_count = current_revisions + 1 if will_retry else current_revisions
        stage_status: Any = "retrying" if will_retry else "completed"

        if will_retry:
            summary = "Requested semantic SQL revision"
            await _emit(
                config,
                "stage_retry",
                {
                    "stage": "sql_generator",
                    "attempt": next_revision_count + state.get("execution_retry_count", 0) + 1,
                    "reason": output.revision_feedback or "Query Reviewer requested revision",
                },
            )
        else:
            summary = (
                "Semantic review approved"
                if output.status == "approved"
                else "Max review revisions reached; proceeding to deterministic Security Gate"
            )

        await _emit(
            config,
            "stage_completed",
            {
                "stage": stage,
                "label": PRIMARY_STAGE_LABELS[stage],
                "status": stage_status,
                "attempt": attempt,
                "duration_ms": duration_ms,
                "summary": summary,
            },
        )

        warnings: list[str] = []
        if output.status == "needs_revision" and not will_retry:
            warnings.append(
                "Query Reviewer requested additional revisions beyond the retry cap; "
                "proceeded to deterministic security validation."
            )

        return {
            "review_status": output.status,
            "review_notes": output.notes,
            "revision_feedback": output.revision_feedback if will_retry else None,
            "revision_count": next_revision_count,
            "warnings": warnings,
            "stages": [
                StageRecord(
                    stage=stage,
                    status=stage_status,
                    attempt=attempt,
                    duration_ms=duration_ms,
                    summary=summary,
                )
            ],
        }

    async def security_gate(
        self,
        state: DetectiveState,
        config: RunnableConfig,
    ) -> dict[str, Any]:
        """Agent 4: 100% deterministic SQLGlot AST security boundary (non-LLM)."""
        stage = "security_gate"
        attempt = state.get("execution_retry_count", 0) + 1
        start = time.perf_counter()
        await _emit(
            config,
            "stage_started",
            {
                "stage": stage,
                "label": PRIMARY_STAGE_LABELS[stage],
                "attempt": attempt,
                "timestamp": _utc_now_iso(),
            },
        )

        validation = self._gate.validate(
            state.get("candidate_sql", ""),
            allowed_schemas=state["allowed_schemas"],
            max_rows=state["max_rows"],
            hard_max_rows=self._hard_max_rows,
        )
        duration_ms = round((time.perf_counter() - start) * 1000.0, 2)

        if not validation.passed or validation.validated_sql is None:
            violations = list(validation.violations)
            summary = f"Blocked by Security Gate ({len(violations)} violation(s))"
            await _emit(
                config,
                "security_blocked",
                {
                    "stage": stage,
                    "label": PRIMARY_STAGE_LABELS[stage],
                    "violations": violations,
                    "sql": state.get("candidate_sql", ""),
                },
            )
            await _emit(
                config,
                "stage_completed",
                {
                    "stage": stage,
                    "label": PRIMARY_STAGE_LABELS[stage],
                    "status": "blocked",
                    "attempt": attempt,
                    "duration_ms": duration_ms,
                    "summary": summary,
                },
            )
            return {
                "security_status": "blocked",
                "security_violations": violations,
                "security_checks": list(validation.checks),
                "validated_sql_artifact": None,
                "normalized_sql": None,
                "enforced_limit": None,
                "limit_was_injected": False,
                "limit_was_clamped": False,
                "execution_status": "skipped",
                "optimization_status": "skipped",
                "stages": [
                    StageRecord(
                        stage=stage,
                        status="blocked",
                        attempt=attempt,
                        duration_ms=duration_ms,
                        summary=summary,
                    )
                ],
            }

        vsql = validation.validated_sql
        summary = (
            f"Passed {len(validation.checks)} deterministic AST checks "
            f"(LIMIT {vsql.enforced_limit})"
        )
        await _emit(
            config,
            "stage_completed",
            {
                "stage": stage,
                "label": PRIMARY_STAGE_LABELS[stage],
                "status": "completed",
                "attempt": attempt,
                "duration_ms": duration_ms,
                "summary": summary,
            },
        )
        return {
            "security_status": "passed",
            "security_violations": [],
            "security_checks": list(validation.checks),
            "validated_sql_artifact": vsql,
            "normalized_sql": vsql.normalized_sql,
            "enforced_limit": vsql.enforced_limit,
            "limit_was_injected": vsql.limit_was_injected,
            "limit_was_clamped": vsql.limit_was_clamped,
            "stages": [
                StageRecord(
                    stage=stage,
                    status="completed",
                    attempt=attempt,
                    duration_ms=duration_ms,
                    summary=summary,
                )
            ],
        }

    async def sql_executor(
        self,
        state: DetectiveState,
        config: RunnableConfig,
    ) -> dict[str, Any]:
        """Agent 5: Deterministic read-only PostgreSQL executor requiring ValidatedSQL."""
        stage = "sql_executor"
        current_retries = state.get("execution_retry_count", 0)
        attempt = current_retries + 1
        start = time.perf_counter()
        await _emit(
            config,
            "stage_started",
            {
                "stage": stage,
                "label": PRIMARY_STAGE_LABELS[stage],
                "attempt": attempt,
                "timestamp": _utc_now_iso(),
            },
        )

        validated_artifact = state.get("validated_sql_artifact")
        cancel_event = _get_cancel_event(config)

        result = await asyncio.to_thread(
            self._executor.execute,
            validated_artifact,  # type: ignore[arg-type]
            self._spec,
            include_explain=state.get("include_explain", True),
            lock_timeout_ms=self._lock_timeout_ms,
            cancel_event=cancel_event,
        )
        duration_ms = round((time.perf_counter() - start) * 1000.0, 2)

        if cancel_event is not None and cancel_event.is_set():
            raise asyncio.CancelledError("Query execution cancelled by client.")

        if result.status == "error" and current_retries < MAX_EXECUTION_RETRIES:
            next_retries = current_retries + 1
            await _emit(
                config,
                "stage_retry",
                {
                    "stage": "sql_generator",
                    "attempt": state.get("revision_count", 0) + next_retries + 1,
                    "reason": f"PostgreSQL execution error: {result.error_message}",
                },
            )
            await _emit(
                config,
                "stage_completed",
                {
                    "stage": stage,
                    "label": PRIMARY_STAGE_LABELS[stage],
                    "status": "retrying",
                    "attempt": attempt,
                    "duration_ms": duration_ms,
                    "summary": "Recoverable SQL error; regenerating query",
                },
            )
            return {
                "execution_status": "error",
                "execution_error": result.error_message,
                "execution_time_ms": result.execution_time_ms,
                "execution_retry_count": next_retries,
                "warnings": list(result.warnings),
                "stages": [
                    StageRecord(
                        stage=stage,
                        status="retrying",
                        attempt=attempt,
                        duration_ms=duration_ms,
                        summary="Recoverable SQL error; regenerating query",
                    )
                ],
            }

        if result.status != "success":
            summary = result.error_message or f"Execution ended with status '{result.status}'"
            await _emit(
                config,
                "stage_completed",
                {
                    "stage": stage,
                    "label": PRIMARY_STAGE_LABELS[stage],
                    "status": "error",
                    "attempt": attempt,
                    "duration_ms": duration_ms,
                    "summary": summary,
                },
            )
            return {
                "execution_status": result.status,
                "columns": [],
                "rows": [],
                "row_count": 0,
                "was_truncated": False,
                "execution_time_ms": result.execution_time_ms,
                "execution_error": result.error_message,
                "explain_plan": result.explain_plan,
                "plan_summary": result.plan_summary,
                "optimization_status": "skipped",
                "warnings": list(result.warnings),
                "stages": [
                    StageRecord(
                        stage=stage,
                        status="error",
                        attempt=attempt,
                        duration_ms=duration_ms,
                        summary=summary,
                    )
                ],
            }

        summary = f"Returned {result.row_count} row(s) in {result.execution_time_ms:.1f}ms"
        await _emit(
            config,
            "stage_completed",
            {
                "stage": stage,
                "label": PRIMARY_STAGE_LABELS[stage],
                "status": "completed",
                "attempt": attempt,
                "duration_ms": duration_ms,
                "summary": summary,
            },
        )
        return {
            "execution_status": "success",
            "columns": list(result.columns),
            "rows": result.rows,
            "row_count": result.row_count,
            "was_truncated": result.was_truncated,
            "execution_time_ms": result.execution_time_ms,
            "execution_error": None,
            "explain_plan": result.explain_plan,
            "plan_summary": result.plan_summary,
            "warnings": list(result.warnings),
            "stages": [
                StageRecord(
                    stage=stage,
                    status="completed",
                    attempt=attempt,
                    duration_ms=duration_ms,
                    summary=summary,
                )
            ],
        }

    async def result_explainer(
        self,
        state: DetectiveState,
        config: RunnableConfig,
    ) -> dict[str, Any]:
        """Agent 6: Produce grounded plain-language explanation of returned SQL results."""
        stage = "result_explainer"
        start = time.perf_counter()
        await _emit(
            config,
            "stage_started",
            {
                "stage": stage,
                "label": PRIMARY_STAGE_LABELS[stage],
                "attempt": 1,
                "timestamp": _utc_now_iso(),
            },
        )

        sample_rows = state.get("rows", [])[:25]
        prompt = (
            f"User question:\n{state['user_question']}\n\n"
            f"Executed SQL:\n{state.get('normalized_sql', '')}\n\n"
            f"Columns: {state.get('columns', [])}\n"
            f"Returned row count: {state.get('row_count', 0)}\n"
            f"Truncated by limit: {state.get('was_truncated', False)}\n"
            f"Execution time (ms): {state.get('execution_time_ms')}\n\n"
            f"Result sample (up to 25 rows):\n{json.dumps(sample_rows, default=str)}"
        )

        try:
            output = await _invoke_structured(
                self._get_active_llm(),
                ResultExplanationOutput,
                RESULT_EXPLAINER_SYSTEM_PROMPT,
                prompt,
                timeout_seconds=self._llm_timeout_seconds,
            )
            duration_ms = round((time.perf_counter() - start) * 1000.0, 2)
            summary = "Generated grounded explanation of query results"
            await _emit(
                config,
                "stage_completed",
                {
                    "stage": stage,
                    "label": PRIMARY_STAGE_LABELS[stage],
                    "status": "completed",
                    "attempt": 1,
                    "duration_ms": duration_ms,
                    "summary": summary,
                },
            )
            return {
                "explanation_summary": output.summary,
                "key_findings": output.key_findings,
                "caveats": output.caveats,
                "suggested_chart": output.suggested_chart,
                "stages": [
                    StageRecord(
                        stage=stage,
                        status="completed",
                        attempt=1,
                        duration_ms=duration_ms,
                        summary=summary,
                    )
                ],
            }
        except Exception:
            duration_ms = round((time.perf_counter() - start) * 1000.0, 2)
            logger.warning("Result Explainer degraded gracefully after LLM error.")
            fallback_summary = (
                f"Query executed successfully and returned {state.get('row_count', 0)} row(s)."
            )
            await _emit(
                config,
                "stage_completed",
                {
                    "stage": stage,
                    "label": PRIMARY_STAGE_LABELS[stage],
                    "status": "completed",
                    "attempt": 1,
                    "duration_ms": duration_ms,
                    "summary": "Returned deterministic fallback summary",
                },
            )
            return {
                "explanation_summary": fallback_summary,
                "key_findings": [],
                "caveats": ["AI narrative explanation was temporarily unavailable."],
                "suggested_chart": "none",
                "warnings": ["Result Explainer fell back to a basic summary."],
                "stages": [
                    StageRecord(
                        stage=stage,
                        status="completed",
                        attempt=1,
                        duration_ms=duration_ms,
                        summary="Returned deterministic fallback summary",
                    )
                ],
            }

    async def optimization_agent(
        self,
        state: DetectiveState,
        config: RunnableConfig,
    ) -> dict[str, Any]:
        """Agent 7: Parallel EXPLAIN (FORMAT JSON) optimization synthesis.

        Executes in parallel with Result Explainer and degrades gracefully to
        deterministic plan_parser findings so it never blocks or fails the workflow.
        """
        start = time.perf_counter()
        await _emit(
            config,
            "optimization_started",
            {"stage": "optimization_agent", "timestamp": _utc_now_iso()},
        )

        explain_plan = state.get("explain_plan")
        plan_summary = state.get("plan_summary")
        deterministic_recs = _deterministic_findings_as_recommendations(plan_summary)

        if not explain_plan:
            duration_ms = round((time.perf_counter() - start) * 1000.0, 2)
            await _emit(
                config,
                "optimization_completed",
                {
                    "stage": "optimization_agent",
                    "status": "skipped",
                    "duration_ms": duration_ms,
                    "recommendation_count": 0,
                    "recommendations": [],
                },
            )
            return {
                "optimization_status": "skipped",
                "optimization_recommendations": [],
            }

        prompt = (
            f"Executed SQL:\n{state.get('normalized_sql', '')}\n\n"
            f"EXPLAIN (FORMAT JSON) plan:\n{json.dumps(explain_plan, default=str)}\n\n"
            f"Deterministic plan findings:\n{json.dumps(deterministic_recs)}\n\n"
            f"Schema & index metadata:\n{state['schema_prompt']}"
        )

        # Bound optimization synthesis tightly so it never stalls workflow completion.
        opt_timeout = min(self._llm_timeout_seconds, 12)
        try:
            output = await _invoke_structured(
                self._get_active_llm(),
                OptimizationSynthesisOutput,
                OPTIMIZATION_AGENT_SYSTEM_PROMPT,
                prompt,
                timeout_seconds=opt_timeout,
            )
            recs = [item.model_dump() for item in output.recommendations] or deterministic_recs
            duration_ms = round((time.perf_counter() - start) * 1000.0, 2)
            await _emit(
                config,
                "optimization_completed",
                {
                    "stage": "optimization_agent",
                    "status": "completed",
                    "duration_ms": duration_ms,
                    "recommendation_count": len(recs),
                    "recommendations": recs,
                },
            )
            return {
                "optimization_status": "completed",
                "optimization_recommendations": recs,
            }
        except Exception:
            duration_ms = round((time.perf_counter() - start) * 1000.0, 2)
            logger.warning("Optimization Agent degraded gracefully to deterministic plan findings.")
            await _emit(
                config,
                "optimization_completed",
                {
                    "stage": "optimization_agent",
                    "status": "partial",
                    "duration_ms": duration_ms,
                    "recommendation_count": len(deterministic_recs),
                    "recommendations": deterministic_recs,
                },
            )
            return {
                "optimization_status": "partial",
                "optimization_recommendations": deterministic_recs,
                "warnings": [
                    "Optimization Agent used deterministic EXPLAIN (FORMAT JSON) findings only."
                ],
            }
