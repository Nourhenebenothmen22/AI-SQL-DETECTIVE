import asyncio
import logging
import threading
from collections.abc import Callable
from typing import Any
from uuid import UUID

import psycopg
from langchain_core.language_models.chat_models import BaseChatModel

from app.core.config import Settings
from app.core.context import RequestContext
from app.modules.ai.graph import build_detective_graph
from app.modules.ai.llm import build_chat_model, configure_langsmith_tracing
from app.modules.ai.nodes import EventEmitter
from app.modules.ai.state import DetectiveState
from app.modules.connections.registry import DatabaseConnectionSpec
from app.modules.database.introspector import format_compact_schema_prompt, introspect_schema
from app.modules.execution.executor import SQLExecutor
from app.modules.execution.plan_parser import PlanSummary
from app.modules.history.repository import QueryRunRecordInput, QueryRunRepository
from app.modules.security.gate import SecurityGate
from app.schemas.queries import (
    AskQueryResponse,
    ExplanationResponse,
    OptimizationRecommendationResponse,
    PlanFindingResponse,
    PlanSummaryResponse,
    QueryClassificationResponse,
    SecurityCheckResponse,
    StageStatusResponse,
)

logger = logging.getLogger(__name__)

LLMFactory = Callable[[Settings], BaseChatModel]


class SchemaUnavailableError(RuntimeError):
    """Raised when live schema introspection fails before workflow start."""


def to_plan_summary_response(summary: PlanSummary | None) -> PlanSummaryResponse | None:
    if summary is None:
        return None
    return PlanSummaryResponse(
        root_node_type=summary.root_node_type,
        startup_cost=summary.startup_cost,
        total_cost=summary.total_cost,
        estimated_rows=summary.estimated_rows,
        plan_width=summary.plan_width,
        node_types=list(summary.node_types),
        has_sort=summary.has_sort,
        has_nested_loop=summary.has_nested_loop,
        has_hash_join=summary.has_hash_join,
        findings=[
            PlanFindingResponse(
                severity=finding.severity,
                category=finding.category,
                title=finding.title,
                detail=finding.detail,
                suggestion=finding.suggestion,
            )
            for finding in summary.findings
        ],
    )


class DetectiveWorkflowService:
    """Orchestrates the 7-agent LangGraph pipeline with timeout, cancel, and telemetry."""

    def __init__(
        self,
        *,
        settings: Settings,
        security_gate: SecurityGate,
        sql_executor: SQLExecutor,
        history_repo: QueryRunRepository,
        llm_factory: LLMFactory = build_chat_model,
    ) -> None:
        self._settings = settings
        self._gate = security_gate
        self._executor = sql_executor
        self._history_repo = history_repo
        self._llm_factory = llm_factory

    def _record_interrupted_run(
        self,
        *,
        spec: DatabaseConnectionSpec,
        context: RequestContext,
        question: str,
        status: Any,
    ) -> UUID | None:
        return self._history_repo.record_run(
            QueryRunRecordInput(
                connection_id=spec.id,
                actor_id=context.actor_id,
                mode="nl",
                natural_language_prompt=question,
                security_status="passed",
                execution_status=status,
            )
        )

    async def run_workflow(
        self,
        *,
        question: str,
        spec: DatabaseConnectionSpec,
        context: RequestContext,
        max_rows: int | None = None,
        include_explain: bool = True,
        event_emitter: EventEmitter | None = None,
        cancel_event: threading.Event | None = None,
    ) -> AskQueryResponse:
        configure_langsmith_tracing(self._settings)
        llm = self._llm_factory(self._settings)

        try:
            schema = await asyncio.to_thread(introspect_schema, spec)
        except (psycopg.Error, OSError) as exc:
            logger.warning("Schema introspection failed before AI workflow on %s.", spec.id)
            raise SchemaUnavailableError(
                "Unable to introspect target database schema before starting AI workflow."
            ) from exc

        schema_prompt = format_compact_schema_prompt(schema)
        requested_max = max_rows if max_rows is not None else spec.max_rows

        graph = build_detective_graph(
            llm=llm,
            security_gate=self._gate,
            sql_executor=self._executor,
            connection_spec=spec,
            hard_max_rows=self._settings.sql_hard_max_rows,
            lock_timeout_ms=self._settings.sql_lock_timeout_ms,
            llm_timeout_seconds=self._settings.llm_timeout_seconds,
        )

        initial_state: DetectiveState = {
            "connection_id": spec.id,
            "user_question": question.strip(),
            "max_rows": requested_max,
            "include_explain": include_explain,
            "schema_prompt": schema_prompt,
            "allowed_schemas": list(spec.target_schemas),
            "revision_count": 0,
            "execution_retry_count": 0,
            "warnings": [],
            "stages": [],
        }

        config: dict[str, Any] = {
            "configurable": {
                "event_emitter": event_emitter,
                "cancel_event": cancel_event,
            },
            "run_name": "ai-sql-detective-workflow",
            "metadata": {
                "connection_id": spec.id,
                "actor_id": context.actor_id,
                "llm_provider": self._settings.llm_provider,
                "llm_model": self._settings.llm_model,
            },
        }

        try:
            final_state: DetectiveState = await asyncio.wait_for(
                graph.ainvoke(initial_state, config=config),
                timeout=self._settings.workflow_timeout_seconds,
            )
        except TimeoutError:
            if cancel_event is not None:
                cancel_event.set()
            self._record_interrupted_run(
                spec=spec,
                context=context,
                question=question.strip(),
                status="timeout",
            )
            raise
        except asyncio.CancelledError:
            if cancel_event is not None:
                cancel_event.set()
            self._record_interrupted_run(
                spec=spec,
                context=context,
                question=question.strip(),
                status="cancelled",
            )
            raise

        security_status = final_state.get("security_status", "blocked")
        execution_status = final_state.get("execution_status", "skipped")
        optimizations_raw = final_state.get("optimization_recommendations") or []

        run_id = self._history_repo.record_run(
            QueryRunRecordInput(
                connection_id=spec.id,
                actor_id=context.actor_id,
                mode="nl",
                natural_language_prompt=question.strip(),
                generated_sql=final_state.get("candidate_sql"),
                validated_sql=final_state.get("normalized_sql"),
                security_status=security_status,
                security_violations=final_state.get("security_violations") or None,
                review_status=final_state.get("review_status"),
                execution_status=execution_status,
                execution_time_ms=final_state.get("execution_time_ms"),
                row_count=final_state.get("row_count"),
                was_truncated=bool(final_state.get("was_truncated", False)),
                explain_plan=final_state.get("explain_plan"),
                explanation_text=final_state.get("explanation_summary"),
                optimizations=optimizations_raw or None,
            )
        )

        explanation_resp: ExplanationResponse | None = None
        if final_state.get("explanation_summary"):
            explanation_resp = ExplanationResponse(
                summary=final_state["explanation_summary"] or "",
                key_findings=final_state.get("key_findings", []),
                caveats=final_state.get("caveats", []),
                suggested_chart=final_state.get("suggested_chart", "none"),
            )

        security_checks = [
            SecurityCheckResponse(rule=c.rule, passed=c.passed, detail=c.detail)
            for c in final_state.get("security_checks", [])
        ]

        classification_resp: QueryClassificationResponse | None = None
        if final_state.get("query_intent"):
            classification_resp = QueryClassificationResponse(
                intent=final_state.get("query_intent", "general"),
                complexity=final_state.get("query_complexity", "moderate"),
                recommended_strategy=final_state.get("recommended_strategy", ""),
            )

        return AskQueryResponse(
            run_id=run_id,
            connection_id=spec.id,
            question=question.strip(),
            classification=classification_resp,
            selected_tables=final_state.get("selected_tables", []),
            ambiguities=final_state.get("ambiguities", []),
            candidate_sql=final_state.get("candidate_sql"),
            validated_sql=final_state.get("normalized_sql"),
            generation_rationale=final_state.get("generation_rationale"),
            assumptions=final_state.get("assumptions", []),
            review_status=final_state.get("review_status"),
            review_notes=final_state.get("review_notes", []),
            security_status=security_status,
            security_violations=final_state.get("security_violations", []),
            security_checks=security_checks,
            enforced_limit=final_state.get("enforced_limit"),
            limit_was_injected=bool(final_state.get("limit_was_injected", False)),
            limit_was_clamped=bool(final_state.get("limit_was_clamped", False)),
            execution_status=execution_status,
            columns=final_state.get("columns", []),
            rows=final_state.get("rows", []),
            row_count=final_state.get("row_count", 0),
            was_truncated=bool(final_state.get("was_truncated", False)),
            execution_time_ms=final_state.get("execution_time_ms"),
            execution_error=final_state.get("execution_error"),
            explanation=explanation_resp,
            explain_plan=final_state.get("explain_plan"),
            plan_summary=to_plan_summary_response(final_state.get("plan_summary")),
            optimization_status=final_state.get("optimization_status", "skipped"),
            optimizations=[
                OptimizationRecommendationResponse.model_validate(item)
                for item in optimizations_raw
            ],
            warnings=final_state.get("warnings", []),
            stages=[StageStatusResponse(**stage) for stage in final_state.get("stages", [])],
        )
