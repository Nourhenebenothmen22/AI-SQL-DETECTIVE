from dataclasses import replace

import psycopg
import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import load_settings, to_psycopg_dsn
from app.main import create_app
from app.modules.connections.registry import ConnectionRegistry
from app.modules.execution.executor import SQLExecutor
from app.modules.history.repository import QueryRunRecordInput, QueryRunRepository
from app.modules.security.gate import SecurityGate


@pytest.mark.integration
async def test_live_execute_endpoint_runs_readonly_query_with_explain_and_telemetry() -> None:
    settings = load_settings()
    app = create_app(settings=settings)
    transport = ASGITransport(app=app)

    sql = (
        "SELECT status, COUNT(*) AS order_count, ROUND(SUM(total_amount), 2) AS revenue "
        "FROM ecommerce.orders "
        "WHERE placed_at >= '2025-01-01'::timestamptz "
        "GROUP BY status "
        "ORDER BY revenue DESC"
    )
    try:
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.post("/api/v1/queries/execute", json={"sql": sql})
    finally:
        app.state.query_run_repository.dispose()

    assert response.status_code == 200
    payload = response.json()
    assert payload["security_status"] == "passed"
    assert payload["execution_status"] == "success"
    assert payload["row_count"] >= 1
    assert payload["columns"] == ["status", "order_count", "revenue"]
    assert payload["execution_time_ms"] is not None
    assert payload["explain_plan"] is not None
    assert payload["plan_summary"] is not None
    # Verify EXPLAIN (FORMAT JSON) was used, NEVER automatic EXPLAIN ANALYZE.
    assert "Actual Total Time" not in response.text
    assert payload["run_id"] is not None

    # Verify telemetry row was persisted in app_meta.query_runs via sql_detective_app.
    app_dsn = to_psycopg_dsn(settings.database_app_url.get_secret_value())
    with psycopg.connect(app_dsn, connect_timeout=5) as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT security_status, execution_status, row_count "
            "FROM app_meta.query_runs WHERE id = %s",
            (payload["run_id"],),
        )
        row = cur.fetchone()
        assert row == ("passed", "success", payload["row_count"])


@pytest.mark.integration
async def test_live_execute_enforces_exact_row_truncation_without_boundary_false_positive() -> None:
    settings = load_settings()
    app = create_app(settings=settings)
    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            # ecommerce.products has exactly 200 rows: max_rows=200 must NOT report truncation.
            exact_resp = await client.post(
                "/api/v1/queries/execute",
                json={"sql": "SELECT id, sku FROM ecommerce.products", "max_rows": 200},
            )
            # max_rows=199 MUST report truncation because 1 more row exists.
            truncated_resp = await client.post(
                "/api/v1/queries/execute",
                json={"sql": "SELECT id, sku FROM ecommerce.products", "max_rows": 199},
            )
    finally:
        app.state.query_run_repository.dispose()

    assert exact_resp.status_code == 200
    exact_payload = exact_resp.json()
    assert exact_payload["execution_status"] == "success"
    assert exact_payload["row_count"] == 200
    assert exact_payload["enforced_limit"] == 200
    assert exact_payload["limit_was_injected"] is True
    assert exact_payload["was_truncated"] is False

    assert truncated_resp.status_code == 200
    trunc_payload = truncated_resp.json()
    assert trunc_payload["execution_status"] == "success"
    assert trunc_payload["row_count"] == 199
    assert trunc_payload["enforced_limit"] == 199
    assert trunc_payload["was_truncated"] is True


@pytest.mark.integration
async def test_live_execute_blocks_destructive_sql_and_preserves_data() -> None:
    settings = load_settings()
    app = create_app(settings=settings)
    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.post(
                "/api/v1/queries/execute",
                json={"sql": "DELETE FROM ecommerce.orders WHERE id > 0"},
            )
    finally:
        app.state.query_run_repository.dispose()

    assert response.status_code == 200
    payload = response.json()
    assert payload["security_status"] == "blocked"
    assert payload["execution_status"] == "skipped"
    assert payload["run_id"] is not None

    # Confirm all 12,000 orders remain intact.
    ro_dsn = to_psycopg_dsn(settings.database_ro_url.get_secret_value())
    with psycopg.connect(ro_dsn, connect_timeout=5) as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM ecommerce.orders")
        assert cur.fetchone() == (12000,)


@pytest.mark.integration
def test_live_executor_enforces_statement_timeout() -> None:
    settings = load_settings()
    registry = ConnectionRegistry(settings)
    tight_spec = replace(registry.get(), statement_timeout_ms=50)

    gate = SecurityGate()
    validation = gate.validate(
        "SELECT COUNT(*) FROM generate_series(1, 5000) a CROSS JOIN generate_series(1, 5000) b",
        allowed_schemas=tight_spec.target_schemas,
        max_rows=10,
    )
    assert validation.passed is True
    assert validation.validated_sql is not None

    executor = SQLExecutor()
    result = executor.execute(validation.validated_sql, tight_spec, include_explain=False)
    assert result.status == "timeout"
    assert result.error_message is not None
    assert "timeout" in result.error_message.lower()


@pytest.mark.integration
def test_live_app_meta_accepts_cancelled_execution_status() -> None:
    settings = load_settings()
    repo = QueryRunRepository(settings)
    try:
        run_id = repo.record_run(
            QueryRunRecordInput(
                connection_id="ecommerce_demo",
                actor_id="local-dev",
                mode="nl",
                natural_language_prompt="Top customers by spend",
                security_status="passed",
                execution_status="cancelled",
            )
        )
        assert run_id is not None
    finally:
        repo.dispose()

    app_dsn = to_psycopg_dsn(settings.database_app_url.get_secret_value())
    with psycopg.connect(app_dsn, connect_timeout=5) as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT execution_status FROM app_meta.query_runs WHERE id = %s",
            (run_id,),
        )
        assert cur.fetchone() == ("cancelled",)
