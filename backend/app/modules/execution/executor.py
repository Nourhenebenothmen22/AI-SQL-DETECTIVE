import logging
import threading
import time
from dataclasses import dataclass
from datetime import date, datetime
from datetime import time as dt_time
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

import psycopg

from app.core.config import to_psycopg_dsn
from app.modules.connections.registry import DatabaseConnectionSpec
from app.modules.execution.plan_parser import PlanSummary, analyze_explain_plan
from app.modules.security.types import ValidatedSQL, verify_validated_sql

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    """Result of executing a SecurityGate-validated read-only SQL query."""

    status: Literal["success", "error", "timeout"]
    columns: tuple[str, ...]
    rows: list[dict[str, Any]]
    row_count: int
    was_truncated: bool
    execution_time_ms: float
    error_message: str | None = None
    explain_plan: list[dict[str, Any]] | None = None
    plan_summary: PlanSummary | None = None
    warnings: tuple[str, ...] = ()


def _serialize_cell(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date, dt_time)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, (bytes, bytearray, memoryview)):
        return bytes(value).hex()
    if isinstance(value, (list, tuple)):
        return [_serialize_cell(item) for item in value]
    if isinstance(value, dict):
        return {str(k): _serialize_cell(v) for k, v in value.items()}
    return str(value)


def _unique_column_names(raw_names: list[str]) -> tuple[str, ...]:
    seen: dict[str, int] = {}
    unique: list[str] = []
    for name in raw_names:
        count = seen.get(name, 0)
        seen[name] = count + 1
        unique.append(name if count == 0 else f"{name}_{count + 1}")
    return tuple(unique)


class SQLExecutor:
    """Deterministic read-only PostgreSQL executor.

    Structurally refuses raw SQL strings—only sealed ValidatedSQL artifacts
    minted by SecurityGate.validate() are accepted. Uses EXPLAIN (FORMAT JSON)
    exclusively and never runs EXPLAIN ANALYZE automatically.
    """

    def execute(
        self,
        validated_sql: ValidatedSQL,
        spec: DatabaseConnectionSpec,
        *,
        include_explain: bool = True,
        lock_timeout_ms: int = 1000,
        cancel_event: threading.Event | None = None,
    ) -> ExecutionResult:
        verified = verify_validated_sql(validated_sql)
        dsn = to_psycopg_dsn(spec.dsn.get_secret_value())
        warnings: list[str] = []
        explain_plan: list[dict[str, Any]] | None = None
        plan_summary: PlanSummary | None = None

        if cancel_event is not None and cancel_event.is_set():
            return ExecutionResult(
                status="error",
                columns=(),
                rows=[],
                row_count=0,
                was_truncated=False,
                execution_time_ms=0.0,
                error_message="Query execution cancelled before start.",
            )

        start = time.perf_counter()
        cancel_watcher_stop = threading.Event()
        try:
            with psycopg.connect(dsn, connect_timeout=5) as conn:
                watcher_thread: threading.Thread | None = None
                if cancel_event is not None:

                    def _watch_cancel() -> None:
                        while not cancel_watcher_stop.is_set():
                            if cancel_event.wait(timeout=0.05):
                                try:
                                    conn.cancel()
                                except Exception:
                                    logger.debug("Best-effort psycopg cancel ignored.")
                                return

                    watcher_thread = threading.Thread(target=_watch_cancel, daemon=True)
                    watcher_thread.start()

                try:
                    with conn.cursor() as cur:
                        cur.execute("BEGIN TRANSACTION READ ONLY")
                        cur.execute(
                            "SELECT set_config('statement_timeout', %s, true)",
                            (f"{spec.statement_timeout_ms}ms",),
                        )
                        cur.execute(
                            "SELECT set_config('lock_timeout', %s, true)",
                            (f"{lock_timeout_ms}ms",),
                        )

                        # Safe query-plan inspection ONLY (never automatic EXPLAIN ANALYZE).
                        if include_explain:
                            cur.execute("SAVEPOINT explain_sp")
                            try:
                                cur.execute(f"EXPLAIN (FORMAT JSON) {verified.normalized_sql}")
                                plan_row = cur.fetchone()
                                if plan_row and isinstance(plan_row[0], list):
                                    explain_plan = plan_row[0]
                                    plan_summary = analyze_explain_plan(
                                        explain_plan,
                                        sql=verified.original_sql,
                                        has_select_star=verified.has_select_star,
                                    )
                                cur.execute("RELEASE SAVEPOINT explain_sp")
                            except psycopg.Error:
                                cur.execute("ROLLBACK TO SAVEPOINT explain_sp")
                                warnings.append(
                                    "EXPLAIN (FORMAT JSON) plan inspection was unavailable for "
                                    "this query."
                                )

                        query_start = time.perf_counter()
                        cur.execute(verified.execution_sql)
                        raw_col_names = [desc.name for desc in (cur.description or ())]
                        columns = _unique_column_names(raw_col_names)

                        # Fetch up to enforced_limit + 1 rows so truncation is exact even on
                        # exact-boundary tables (e.g., 200 rows with LIMIT 200 -> not truncated).
                        fetched = cur.fetchmany(verified.enforced_limit + 1)
                        elapsed_ms = round((time.perf_counter() - query_start) * 1000.0, 2)

                        was_truncated = len(fetched) > verified.enforced_limit
                        if was_truncated:
                            fetched = fetched[: verified.enforced_limit]

                        rows = [
                            {
                                col: _serialize_cell(val)
                                for col, val in zip(columns, row, strict=True)
                            }
                            for row in fetched
                        ]

                    conn.rollback()
                finally:
                    cancel_watcher_stop.set()
                    if watcher_thread is not None:
                        watcher_thread.join(timeout=0.5)

            return ExecutionResult(
                status="success",
                columns=columns,
                rows=rows,
                row_count=len(rows),
                was_truncated=was_truncated,
                execution_time_ms=elapsed_ms,
                explain_plan=explain_plan,
                plan_summary=plan_summary,
                warnings=tuple(warnings),
            )

        except psycopg.errors.QueryCanceled:
            elapsed_ms = round((time.perf_counter() - start) * 1000.0, 2)
            if cancel_event is not None and cancel_event.is_set():
                return ExecutionResult(
                    status="error",
                    columns=(),
                    rows=[],
                    row_count=0,
                    was_truncated=False,
                    execution_time_ms=elapsed_ms,
                    error_message="Query execution cancelled by client.",
                    explain_plan=explain_plan,
                    plan_summary=plan_summary,
                    warnings=tuple(warnings),
                )
            logger.warning(
                "Query timed out on connection_id=%s after %sms.",
                spec.id,
                spec.statement_timeout_ms,
            )
            return ExecutionResult(
                status="timeout",
                columns=(),
                rows=[],
                row_count=0,
                was_truncated=False,
                execution_time_ms=elapsed_ms,
                error_message=(
                    f"Query exceeded statement timeout of {spec.statement_timeout_ms}ms "
                    "and was cancelled."
                ),
                explain_plan=explain_plan,
                plan_summary=plan_summary,
                warnings=tuple(warnings),
            )

        except psycopg.Error as exc:
            elapsed_ms = round((time.perf_counter() - start) * 1000.0, 2)
            pg_msg = (exc.diag.message_primary if exc.diag else None) or str(exc).splitlines()[0]
            logger.warning("Read-only SQL execution error on connection_id=%s.", spec.id)
            return ExecutionResult(
                status="error",
                columns=(),
                rows=[],
                row_count=0,
                was_truncated=False,
                execution_time_ms=elapsed_ms,
                error_message=pg_msg,
                explain_plan=explain_plan,
                plan_summary=plan_summary,
                warnings=tuple(warnings),
            )
