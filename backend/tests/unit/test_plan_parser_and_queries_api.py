import pytest
from httpx import AsyncClient

from app.modules.execution.plan_parser import analyze_explain_plan
from tests.conftest import FakeQueryRunRepository


def test_plan_parser_extracts_seq_scan_sort_and_wildcard_findings() -> None:
    sample_plan = [
        {
            "Plan": {
                "Node Type": "Sort",
                "Startup Cost": 410.0,
                "Total Cost": 455.2,
                "Plan Rows": 1800,
                "Plan Width": 64,
                "Plans": [
                    {
                        "Node Type": "Seq Scan",
                        "Relation Name": "orders",
                        "Startup Cost": 0.0,
                        "Total Cost": 405.0,
                        "Plan Rows": 1800,
                        "Plan Width": 64,
                        "Filter": "((status)::text = 'delivered'::text)",
                    }
                ],
            }
        }
    ]

    summary = analyze_explain_plan(
        sample_plan,
        sql="SELECT * FROM ecommerce.orders WHERE status = 'delivered' ORDER BY placed_at DESC",
    )
    assert summary is not None
    assert summary.root_node_type == "Sort"
    assert summary.total_cost == 455.2
    assert summary.has_sort is True
    assert len(summary.sequential_scans) == 1
    assert summary.sequential_scans[0].relation_name == "orders"

    categories = {finding.category for finding in summary.findings}
    assert {"indexing", "sorting", "projection"}.issubset(categories)

    # Verify AST wildcard detection does not false-positive on COUNT(*) or string literals.
    count_summary = analyze_explain_plan(
        sample_plan,
        sql="SELECT COUNT(*), 'select *' AS literal_text FROM ecommerce.orders",
    )
    assert count_summary is not None
    assert "projection" not in {finding.category for finding in count_summary.findings}

    alias_star_summary = analyze_explain_plan(
        sample_plan,
        sql="SELECT o.* FROM ecommerce.orders o",
    )
    assert alias_star_summary is not None
    assert "projection" in {finding.category for finding in alias_star_summary.findings}


async def test_validate_endpoint_passes_safe_sql_and_blocks_destructive_sql(
    async_client: AsyncClient,
) -> None:
    safe_resp = await async_client.post(
        "/api/v1/queries/validate",
        json={"sql": "SELECT id, status FROM ecommerce.orders"},
    )
    assert safe_resp.status_code == 200
    safe_body = safe_resp.json()
    assert safe_body["security_status"] == "passed"
    assert safe_body["enforced_limit"] == 200
    assert safe_body["limit_was_injected"] is True

    blocked_resp = await async_client.post(
        "/api/v1/queries/validate",
        json={"sql": "DROP TABLE ecommerce.orders"},
    )
    assert blocked_resp.status_code == 200
    blocked_body = blocked_resp.json()
    assert blocked_body["security_status"] == "blocked"
    assert blocked_body["validated_sql"] is None
    assert len(blocked_body["violations"]) >= 1


async def test_execute_endpoint_never_invokes_executor_for_blocked_sql(
    async_client: AsyncClient,
    fake_history_repo: FakeQueryRunRepository,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _must_not_run(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("SQLExecutor.execute must NEVER be called for blocked SQL.")

    monkeypatch.setattr("app.modules.execution.executor.SQLExecutor.execute", _must_not_run)

    response = await async_client.post(
        "/api/v1/queries/execute",
        json={"sql": "SELECT * FROM app_meta.query_runs"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["security_status"] == "blocked"
    assert payload["execution_status"] == "skipped"
    assert payload["rows"] == []
    assert payload["run_id"] is not None
    assert len(fake_history_repo.records) == 1
    assert fake_history_repo.records[0].security_status == "blocked"
    assert fake_history_repo.records[0].execution_status == "skipped"
    assert "mock_ro_secret" not in response.text


async def test_execute_endpoint_returns_404_for_unknown_connection(
    async_client: AsyncClient,
) -> None:
    response = await async_client.post(
        "/api/v1/queries/execute",
        json={"sql": "SELECT 1", "connection_id": "unknown_db"},
    )
    assert response.status_code == 404
