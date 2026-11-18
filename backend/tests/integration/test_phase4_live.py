import json
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import load_settings
from app.main import create_app
from app.modules.ai.schemas import (
    OptimizationRecommendationItem,
    OptimizationSynthesisOutput,
    QueryReviewOutput,
    ResultExplanationOutput,
    SchemaAnalysisOutput,
    SQLGenerationOutput,
)
from app.modules.ai.service import DetectiveWorkflowService
from tests.unit.test_ai_workflow import FakeStructuredLLM


def _parse_sse(raw_body: str) -> list[tuple[str, dict[str, Any]]]:
    events: list[tuple[str, dict[str, Any]]] = []
    for block in raw_body.strip().split("\n\n"):
        event_name = ""
        data_lines: list[str] = []
        for line in block.splitlines():
            if line.startswith(":"):
                continue
            if line.startswith("event: "):
                event_name = line.removeprefix("event: ").strip()
            elif line.startswith("data: "):
                data_lines.append(line.removeprefix("data: "))
        if event_name and data_lines:
            events.append((event_name, json.loads("\n".join(data_lines))))
    return events


@pytest.mark.integration
async def test_live_sse_workflow_history_and_analytics_end_to_end() -> None:
    settings = load_settings()
    app = create_app(settings=settings)

    fake_llm = FakeStructuredLLM(
        {
            SchemaAnalysisOutput: lambda _m: SchemaAnalysisOutput(
                selected_tables=["ecommerce.orders", "ecommerce.customers"],
                relevant_columns=[
                    "ecommerce.customers.segment",
                    "ecommerce.orders.total_amount",
                    "ecommerce.orders.status",
                ],
                join_paths=["ecommerce.orders.customer_id = ecommerce.customers.id"],
            ),
            SQLGenerationOutput: lambda _m: SQLGenerationOutput(
                sql=(
                    "SELECT c.segment, COUNT(o.id) AS order_count, "
                    "ROUND(SUM(o.total_amount), 2) AS total_revenue "
                    "FROM ecommerce.orders o "
                    "JOIN ecommerce.customers c ON c.id = o.customer_id "
                    "WHERE o.status = 'delivered' "
                    "GROUP BY c.segment "
                    "ORDER BY total_revenue DESC"
                ),
                rationale="Aggregates delivered order counts and revenue by customer segment.",
                assumptions=["Restricted to delivered orders."],
            ),
            QueryReviewOutput: lambda _m: QueryReviewOutput(
                status="approved",
                notes=["Join key and aggregation columns are valid."],
            ),
            ResultExplanationOutput: lambda _m: ResultExplanationOutput(
                summary="Retail customers generate the highest total delivered revenue.",
                key_findings=["Delivered orders are grouped across retail, vip, and wholesale."],
                caveats=["Filtered to delivered orders only."],
                suggested_chart="bar",
            ),
            OptimizationSynthesisOutput: lambda _m: OptimizationSynthesisOutput(
                recommendations=[
                    OptimizationRecommendationItem(
                        severity="warning",
                        category="indexing",
                        title="Composite index on orders(status, customer_id)",
                        detail="Filtered sequential scan observed on ecommerce.orders.",
                        suggestion="Add an index on ecommerce.orders(status, customer_id).",
                        suggested_sql_or_index=(
                            "CREATE INDEX ix_orders_status_customer "
                            "ON ecommerce.orders (status, customer_id);"
                        ),
                    )
                ]
            ),
        }
    )
    app.state.workflow_service = DetectiveWorkflowService(
        settings=settings,
        security_gate=app.state.security_gate,
        sql_executor=app.state.sql_executor,
        history_repo=app.state.query_run_repository,
        llm_factory=lambda _s: fake_llm,  # type: ignore[arg-type, return-value]
    )

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            sse_resp = await client.post(
                "/api/v1/queries/ask/stream",
                json={"question": "Show delivered revenue by customer segment"},
            )
            assert sse_resp.status_code == 200
            events = _parse_sse(sse_resp.text)
            assert events[-1][0] == "final_result"
            final = events[-1][1]
            assert final["security_status"] == "passed"
            assert final["execution_status"] == "success"
            assert final["row_count"] == 3
            assert final["columns"] == ["segment", "order_count", "total_revenue"]
            assert final["explain_plan"] is not None
            assert "Actual Total Time" not in sse_resp.text
            assert final["optimization_status"] == "completed"
            assert final["run_id"] is not None

            # Verify History list & detail reload from live app_meta.query_runs.
            run_id = final["run_id"]
            hist_resp = await client.get(
                "/api/v1/history",
                params={"connection_id": "ecommerce_demo", "mode": "nl", "limit": 10},
            )
            assert hist_resp.status_code == 200
            hist_body = hist_resp.json()
            assert hist_body["total"] >= 1
            assert any(item["id"] == run_id for item in hist_body["items"])

            detail_resp = await client.get(f"/api/v1/history/{run_id}")
            assert detail_resp.status_code == 200
            detail_body = detail_resp.json()
            assert detail_body["id"] == run_id
            assert detail_body["natural_language_prompt"] == (
                "Show delivered revenue by customer segment"
            )
            assert len(detail_body["optimizations"]) == 1

            # Verify Analytics endpoint aggregates telemetry + live ecommerce catalog stats.
            analytics_resp = await client.get(
                "/api/v1/analytics",
                params={"connection_id": "ecommerce_demo", "days": 14},
            )
            assert analytics_resp.status_code == 200
            analytics = analytics_resp.json()
            assert analytics["connection_id"] == "ecommerce_demo"
            assert analytics["summary"]["total_runs"] >= 1
            assert analytics["summary"]["passed_runs"] >= 1
            assert len(analytics["execution_trends"]) >= 1
            assert len(analytics["query_comparisons"]) >= 1
            assert len(analytics["status_distribution"]) == 4
            assert len(analytics["activity_over_time"]) >= 1
            assert len(analytics["database_statistics"]) == 9
            assert settings.database_ro_url.get_secret_value() not in analytics_resp.text
            assert settings.database_app_url.get_secret_value() not in analytics_resp.text
    finally:
        app.state.query_run_repository.dispose()
