import asyncio
import contextlib
import json
import logging
import threading
from collections.abc import AsyncIterator
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse

from app.api.deps import (
    get_app_settings,
    get_connection_registry,
    get_current_context,
    get_query_run_repository,
    get_security_gate,
    get_sql_executor,
    get_workflow_service,
)
from app.core.config import Settings
from app.core.context import RequestContext
from app.modules.ai.llm import LLMConfigurationError, LLMProviderPackageError
from app.modules.ai.service import (
    DetectiveWorkflowService,
    SchemaUnavailableError,
    to_plan_summary_response,
)
from app.modules.connections.registry import ConnectionRegistry
from app.modules.execution.executor import SQLExecutor
from app.modules.history.repository import QueryRunRecordInput, QueryRunRepository
from app.modules.security.gate import SecurityGate
from app.schemas.queries import (
    AskQueryRequest,
    AskQueryResponse,
    ExecuteSQLRequest,
    ExecuteSQLResponse,
    SecurityCheckResponse,
    ValidateSQLRequest,
    ValidateSQLResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/queries", tags=["queries"])

SSE_HEARTBEAT_INTERVAL_SECONDS = 15.0
SSE_DISCONNECT_POLL_SECONDS = 0.25


def _format_sse(event: str, data: dict[str, Any]) -> str:
    payload = json.dumps(data, default=str)
    return f"event: {event}\ndata: {payload}\n\n"


@router.post("/validate", response_model=ValidateSQLResponse)
def validate_sql(
    payload: ValidateSQLRequest,
    settings: Settings = Depends(get_app_settings),
    registry: ConnectionRegistry = Depends(get_connection_registry),
    gate: SecurityGate = Depends(get_security_gate),
    _context: RequestContext = Depends(get_current_context),
) -> ValidateSQLResponse:
    """Deterministically validate SQL via SQLGlot AST without executing it."""
    try:
        spec = registry.get(payload.connection_id)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown connection_id: {payload.connection_id!r}",
        ) from None

    requested_max = payload.max_rows if payload.max_rows is not None else spec.max_rows
    validation = gate.validate(
        payload.sql,
        allowed_schemas=spec.target_schemas,
        max_rows=requested_max,
        hard_max_rows=settings.sql_hard_max_rows,
    )

    checks = [
        SecurityCheckResponse(rule=c.rule, passed=c.passed, detail=c.detail)
        for c in validation.checks
    ]

    if not validation.passed or validation.validated_sql is None:
        return ValidateSQLResponse(
            connection_id=spec.id,
            security_status="blocked",
            original_sql=payload.sql.strip(),
            violations=list(validation.violations),
            checks=checks,
        )

    vsql = validation.validated_sql
    return ValidateSQLResponse(
        connection_id=spec.id,
        security_status="passed",
        original_sql=vsql.original_sql,
        validated_sql=vsql.normalized_sql,
        enforced_limit=vsql.enforced_limit,
        limit_was_injected=vsql.limit_was_injected,
        limit_was_clamped=vsql.limit_was_clamped,
        violations=[],
        checks=checks,
    )


@router.post("/execute", response_model=ExecuteSQLResponse)
def execute_sql(
    payload: ExecuteSQLRequest,
    settings: Settings = Depends(get_app_settings),
    registry: ConnectionRegistry = Depends(get_connection_registry),
    gate: SecurityGate = Depends(get_security_gate),
    executor: SQLExecutor = Depends(get_sql_executor),
    history_repo: QueryRunRepository = Depends(get_query_run_repository),
    context: RequestContext = Depends(get_current_context),
) -> ExecuteSQLResponse:
    """Validate manual SQL deterministically, execute read-only, and record telemetry."""
    try:
        spec = registry.get(payload.connection_id)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown connection_id: {payload.connection_id!r}",
        ) from None

    requested_max = payload.max_rows if payload.max_rows is not None else spec.max_rows
    validation = gate.validate(
        payload.sql,
        allowed_schemas=spec.target_schemas,
        max_rows=requested_max,
        hard_max_rows=settings.sql_hard_max_rows,
    )

    checks = [
        SecurityCheckResponse(rule=c.rule, passed=c.passed, detail=c.detail)
        for c in validation.checks
    ]

    if not validation.passed or validation.validated_sql is None:
        violations = list(validation.violations)
        run_id = history_repo.record_run(
            QueryRunRecordInput(
                connection_id=spec.id,
                actor_id=context.actor_id,
                mode="manual_sql",
                generated_sql=payload.sql.strip(),
                validated_sql=None,
                security_status="blocked",
                security_violations=violations,
                execution_status="skipped",
            )
        )
        return ExecuteSQLResponse(
            run_id=run_id,
            connection_id=spec.id,
            original_sql=payload.sql.strip(),
            validated_sql=None,
            security_status="blocked",
            security_violations=violations,
            security_checks=checks,
            execution_status="skipped",
        )

    vsql = validation.validated_sql
    result = executor.execute(
        vsql,
        spec,
        include_explain=payload.include_explain,
        lock_timeout_ms=settings.sql_lock_timeout_ms,
    )
    plan_summary_resp = to_plan_summary_response(result.plan_summary)
    optimizations_payload = (
        [finding.model_dump() for finding in plan_summary_resp.findings]
        if plan_summary_resp and plan_summary_resp.findings
        else None
    )

    run_id = history_repo.record_run(
        QueryRunRecordInput(
            connection_id=spec.id,
            actor_id=context.actor_id,
            mode="manual_sql",
            generated_sql=vsql.original_sql,
            validated_sql=vsql.normalized_sql,
            security_status="passed",
            execution_status=result.status,
            execution_time_ms=result.execution_time_ms,
            row_count=result.row_count,
            was_truncated=result.was_truncated,
            explain_plan=result.explain_plan,
            optimizations=optimizations_payload,
        )
    )

    return ExecuteSQLResponse(
        run_id=run_id,
        connection_id=spec.id,
        original_sql=vsql.original_sql,
        validated_sql=vsql.normalized_sql,
        security_status="passed",
        security_violations=[],
        security_checks=checks,
        enforced_limit=vsql.enforced_limit,
        limit_was_injected=vsql.limit_was_injected,
        limit_was_clamped=vsql.limit_was_clamped,
        execution_status=result.status,
        columns=list(result.columns),
        rows=result.rows,
        row_count=result.row_count,
        was_truncated=result.was_truncated,
        execution_time_ms=result.execution_time_ms,
        execution_error=result.error_message,
        explain_plan=result.explain_plan,
        plan_summary=plan_summary_resp,
        warnings=list(result.warnings),
    )


@router.post("/ask", response_model=AskQueryResponse)
async def ask_natural_language(
    payload: AskQueryRequest,
    registry: ConnectionRegistry = Depends(get_connection_registry),
    workflow_service: DetectiveWorkflowService = Depends(get_workflow_service),
    context: RequestContext = Depends(get_current_context),
) -> AskQueryResponse:
    """Execute the full 7-agent LangGraph NL-to-SQL workflow and return typed JSON."""
    try:
        spec = registry.get(payload.connection_id)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown connection_id: {payload.connection_id!r}",
        ) from None

    try:
        return await workflow_service.run_workflow(
            question=payload.question,
            spec=spec,
            context=context,
            max_rows=payload.max_rows,
            include_explain=payload.include_explain,
        )
    except LLMConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from None
    except LLMProviderPackageError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from None
    except SchemaUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from None
    except TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="AI SQL workflow exceeded its overall execution timeout.",
        ) from None


@router.post("/ask/stream")
async def ask_natural_language_stream(
    request: Request,
    payload: AskQueryRequest,
    registry: ConnectionRegistry = Depends(get_connection_registry),
    workflow_service: DetectiveWorkflowService = Depends(get_workflow_service),
    context: RequestContext = Depends(get_current_context),
) -> StreamingResponse:
    """Stream safe 6-stage agent progress + parallel Optimization Agent events via SSE."""
    try:
        spec = registry.get(payload.connection_id)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown connection_id: {payload.connection_id!r}",
        ) from None

    async def event_stream() -> AsyncIterator[str]:
        queue: asyncio.Queue[tuple[str, dict[str, Any]] | None] = asyncio.Queue()
        cancel_event = threading.Event()

        async def emit(event: str, data: dict[str, Any]) -> None:
            await queue.put((event, data))

        async def runner() -> None:
            try:
                final_response = await workflow_service.run_workflow(
                    question=payload.question,
                    spec=spec,
                    context=context,
                    max_rows=payload.max_rows,
                    include_explain=payload.include_explain,
                    event_emitter=emit,
                    cancel_event=cancel_event,
                )
                await queue.put(("final_result", final_response.model_dump(mode="json")))
            except LLMConfigurationError as exc:
                await queue.put(("error", {"code": "llm_not_configured", "message": str(exc)}))
            except LLMProviderPackageError as exc:
                await queue.put(("error", {"code": "provider_missing", "message": str(exc)}))
            except SchemaUnavailableError as exc:
                await queue.put(("error", {"code": "schema_unavailable", "message": str(exc)}))
            except TimeoutError:
                await queue.put(
                    (
                        "error",
                        {
                            "code": "workflow_timeout",
                            "message": "AI SQL workflow exceeded its overall timeout.",
                        },
                    )
                )
            except asyncio.CancelledError:
                await queue.put(
                    (
                        "error",
                        {
                            "code": "cancelled",
                            "message": "AI SQL workflow was cancelled.",
                        },
                    )
                )
                raise
            except Exception:
                logger.exception("Unexpected error during SSE AI SQL workflow.")
                await queue.put(
                    (
                        "error",
                        {
                            "code": "internal_error",
                            "message": "An unexpected error occurred while processing the request.",
                        },
                    )
                )
            finally:
                await queue.put(None)

        task = asyncio.create_task(runner())
        elapsed_since_heartbeat = 0.0
        try:
            while True:
                if await request.is_disconnected():
                    cancel_event.set()
                    task.cancel()
                    break

                try:
                    item = await asyncio.wait_for(
                        queue.get(),
                        timeout=SSE_DISCONNECT_POLL_SECONDS,
                    )
                except TimeoutError:
                    elapsed_since_heartbeat += SSE_DISCONNECT_POLL_SECONDS
                    if elapsed_since_heartbeat >= SSE_HEARTBEAT_INTERVAL_SECONDS:
                        elapsed_since_heartbeat = 0.0
                        yield ": keep-alive\n\n"
                    continue

                elapsed_since_heartbeat = 0.0
                if item is None:
                    break
                event_name, data = item
                yield _format_sse(event_name, data)
        finally:
            if not task.done():
                cancel_event.set()
                task.cancel()
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await task

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
