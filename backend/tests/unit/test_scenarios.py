import asyncio
from collections.abc import Callable
from typing import Any

from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.main import create_app
from app.modules.scenarios.service import ScenarioGeneratorService
from app.schemas.scenarios import (
    ScenarioGenerationOutput,
    SimulatedInventoryAdjustment,
    SimulatedOrder,
    SimulatedOrderItem,
    SimulatedReview,
)


class _FakeStructuredRunnable:
    def __init__(self, handler: Callable[[list[Any]], Any]) -> None:
        self._handler = handler

    async def ainvoke(self, messages: list[Any]) -> Any:
        result = self._handler(messages)
        if asyncio.iscoroutine(result):
            return await result
        return result


class FakeScenarioLLM:
    def __init__(self, output: ScenarioGenerationOutput) -> None:
        self._output = output

    def with_structured_output(self, schema: type[Any]) -> _FakeStructuredRunnable:
        return _FakeStructuredRunnable(lambda _msgs: self._output)


async def test_scenario_generation_api(
    test_settings: Settings,
    monkeypatch: Any,
) -> None:
    fake_output = ScenarioGenerationOutput(
        scenario_title="Black Friday Flash Sale",
        scenario_summary="Simulated high volume surge in electronics",
        business_rationale="Stress testing inventory and order processing",
        suggested_workbench_question="What are the top selling electronics during the flash sale?",
        simulated_orders=[
            SimulatedOrder(
                customer_id=1,
                status="delivered",
                order_date_iso="2026-11-20T10:00:00Z",
                items=[
                    SimulatedOrderItem(product_id=1, quantity=3, unit_price=299.99),
                ],
            )
        ],
        inventory_adjustments=[
            SimulatedInventoryAdjustment(
                product_id=1,
                warehouse="WH-CENTRAL",
                quantity_delta=-3,
            )
        ],
        simulated_reviews=[
            SimulatedReview(
                product_id=1,
                customer_id=1,
                rating=5,
                title="Super fast delivery",
                comment="Received my item during Black Friday without delays!",
            )
        ],
    )

    fake_llm = FakeScenarioLLM(fake_output)
    service = ScenarioGeneratorService(settings=test_settings, llm=fake_llm)  # type: ignore[arg-type]

    # Monkeypatch the DB insertion to verify orchestration without altering test DB
    def _mock_anchors(*args: Any, **kwargs: Any) -> tuple[list[int], list[int]]:
        return [1, 2], [1, 2]

    monkeypatch.setattr(
        ScenarioGeneratorService,
        "_fetch_sample_anchors",
        _mock_anchors,
    )

    app = create_app(settings=test_settings)
    app.state.scenario_service = service

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Mock engine begin block
        class FakeConn:
            def execute(self, *args: Any, **kwargs: Any) -> Any:
                class FakeRes:
                    def __init__(self) -> None:
                        self.inserted_primary_key = [9999]

                return FakeRes()

        class FakeEngine:
            def begin(self) -> Any:
                class CM:
                    def __enter__(self) -> FakeConn:
                        return FakeConn()

                    def __exit__(self, *args: Any) -> None:
                        pass

                return CM()

        monkeypatch.setattr(service, "_get_engine", lambda: FakeEngine())

        resp = await client.post(
            "/api/v1/scenarios/generate",
            json={"scenario_prompt": "Simulate a Black Friday flash sale with high sales"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["scenario_title"] == "Black Friday Flash Sale"
    assert data["impact"]["orders_inserted"] == 1
    assert data["impact"]["order_items_inserted"] == 1
    assert data["impact"]["inventory_updated"] == 1
    assert data["impact"]["reviews_inserted"] == 1
    assert "flash sale" in data["suggested_workbench_question"]


async def test_scenario_reset_api(
    test_settings: Settings,
    monkeypatch: Any,
) -> None:
    app = create_app(settings=test_settings)

    # Monkeypatch reset_to_baseline to avoid live truncate during unit testing
    monkeypatch.setattr(
        ScenarioGeneratorService,
        "reset_to_baseline",
        lambda _s: {
            "status": "reset_complete",
            "message": "Reset to golden seed successful",
            "baseline_counts": {"orders": 12000, "customers": 1200},
        },
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        resp = await client.post("/api/v1/scenarios/reset")

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "reset_complete"
    assert data["baseline_counts"]["orders"] == 12000
