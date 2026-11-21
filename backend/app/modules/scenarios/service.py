import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy import create_engine, select, text, update

from app.core.config import Settings
from app.modules.ai.llm import build_chat_model
from app.modules.database.introspector import clear_schema_cache
from app.modules.database.models.ecommerce import (
    Customer,
    Inventory,
    Order,
    OrderItem,
    Payment,
    Product,
    Review,
)
from app.modules.database.seed import seed_database
from app.schemas.scenarios import (
    ScenarioGenerateRequest,
    ScenarioGenerateResponse,
    ScenarioGenerationOutput,
    ScenarioImpactSummary,
    ScenarioResetResponse,
)

logger = logging.getLogger(__name__)

SCENARIO_GENERATOR_SYSTEM_PROMPT = """You are the AI Scenario & What-If Simulator
for AI SQL Detective (PostgreSQL 16).
Your job is to translate a user's natural language business scenario into realistic,
relational e-commerce records that perfectly ground into the PostgreSQL schema.

Rules:
- Respect foreign keys: Use the provided valid customer IDs and product IDs.
- Generate realistic, diverse data reflecting the scenario requested (e.g. surge, churn).
- Order status strictly in: 'pending', 'paid', 'shipped', 'delivered', 'cancelled', 'refunded'.
- Star ratings must be integers between 1 and 5.
- Provide an engaging title, summary, rationale, and a suggested natural language question
  that the user can ask in the Workbench to see the impact of this scenario.
"""


class ScenarioGeneratorService:
    """Orchestrates AI-driven what-if scenario generation and database state resets."""

    def __init__(
        self,
        *,
        settings: Settings,
        llm: BaseChatModel | None = None,
    ) -> None:
        self._settings = settings
        self._llm = llm

    def _get_llm(self) -> BaseChatModel:
        if self._llm is not None:
            return self._llm
        return build_chat_model(self._settings)

    def _get_engine(self) -> Any:
        db_url = (
            self._settings.database_app_url.get_secret_value()
            if self._settings.database_app_url
            else self._settings.database_ro_url.get_secret_value()
        )
        return create_engine(db_url, pool_pre_ping=True)

    def _fetch_sample_anchors(self, engine: Any) -> tuple[list[int], list[int]]:
        """Fetch sample customer IDs and product IDs to anchor foreign keys."""
        try:
            with engine.connect() as conn:
                cust_ids = [
                    int(r[0]) for r in conn.execute(select(Customer.id).limit(20)).fetchall()
                ]
                prod_ids = [
                    int(r[0]) for r in conn.execute(select(Product.id).limit(30)).fetchall()
                ]
                if cust_ids and prod_ids:
                    return cust_ids, prod_ids
        except Exception as e:
            logger.warning("Could not fetch sample anchor IDs from DB: %s", e)
        return list(range(1, 11)), list(range(1, 21))

    async def generate_scenario(self, request: ScenarioGenerateRequest) -> ScenarioGenerateResponse:
        engine = self._get_engine()
        cust_ids, prod_ids = self._fetch_sample_anchors(engine)

        prompt_context = (
            f"User scenario request:\n{request.scenario_prompt}\n\n"
            f"Valid sample customer IDs to anchor to: {cust_ids}\n"
            f"Valid sample product IDs to anchor to: {prod_ids}\n"
            "Simulate this scenario now with structured output."
        )

        llm = self._get_llm()
        runnable = llm.with_structured_output(ScenarioGenerationOutput)
        messages = [
            SystemMessage(content=SCENARIO_GENERATOR_SYSTEM_PROMPT),
            HumanMessage(content=prompt_context),
        ]
        raw_output = await runnable.ainvoke(messages)
        output = (
            raw_output
            if isinstance(raw_output, ScenarioGenerationOutput)
            else ScenarioGenerationOutput.model_validate(raw_output)
        )

        orders_inserted = 0
        order_items_inserted = 0
        inventory_updated = 0
        reviews_inserted = 0

        # Apply simulated changes atomically in database
        try:
            with engine.begin() as conn:
                for sim_order in output.simulated_orders:
                    # Validate customer_id exists or map to first valid anchor
                    valid_cust_id = (
                        sim_order.customer_id if sim_order.customer_id in cust_ids else cust_ids[0]
                    )
                    subtotal = Decimal("0.00")
                    for it in sim_order.items:
                        subtotal += Decimal(str(round(it.quantity * it.unit_price, 2)))

                    total = subtotal
                    try:
                        order_date = datetime.fromisoformat(
                            sim_order.order_date_iso.replace("Z", "+00:00")
                        )
                    except Exception:
                        order_date = datetime.now(UTC)

                    order_res = conn.execute(
                        Order.__table__.insert().values(
                            customer_id=valid_cust_id,
                            status=sim_order.status,
                            subtotal_amount=subtotal,
                            discount_amount=Decimal("0.00"),
                            shipping_amount=Decimal("0.00"),
                            total_amount=total,
                            currency="USD",
                            placed_at=order_date,
                        )
                    )
                    order_id = order_res.inserted_primary_key[0]
                    orders_inserted += 1

                    for it in sim_order.items:
                        valid_prod_id = it.product_id if it.product_id in prod_ids else prod_ids[0]
                        unit_p = Decimal(str(round(it.unit_price, 2)))
                        line_tot = Decimal(str(round(it.quantity * it.unit_price, 2)))
                        conn.execute(
                            OrderItem.__table__.insert().values(
                                order_id=order_id,
                                product_id=valid_prod_id,
                                quantity=it.quantity,
                                unit_price=unit_p,
                                line_total=line_tot,
                            )
                        )
                        order_items_inserted += 1

                    # If paid/delivered, add payment record
                    if sim_order.status in ("paid", "shipped", "delivered"):
                        conn.execute(
                            Payment.__table__.insert().values(
                                order_id=order_id,
                                payment_method="card",
                                status="captured",
                                amount=total,
                                paid_at=order_date,
                            )
                        )

                for adj in output.inventory_adjustments:
                    valid_prod_id = adj.product_id if adj.product_id in prod_ids else prod_ids[0]
                    conn.execute(
                        update(Inventory)
                        .where(Inventory.product_id == valid_prod_id)
                        .values(
                            stock_quantity=text(
                                f"GREATEST(0, stock_quantity + {int(adj.quantity_delta)})"
                            ),
                            updated_at=datetime.now(UTC),
                        )
                    )
                    inventory_updated += 1

                for rev in output.simulated_reviews:
                    valid_prod_id = rev.product_id if rev.product_id in prod_ids else prod_ids[0]
                    valid_cust_id = rev.customer_id if rev.customer_id in cust_ids else cust_ids[0]
                    conn.execute(
                        Review.__table__.insert().values(
                            product_id=valid_prod_id,
                            customer_id=valid_cust_id,
                            rating=max(1, min(5, rev.rating)),
                            comment=f"{rev.title} - {rev.comment}",
                            is_verified_purchase=True,
                            created_at=datetime.now(UTC),
                        )
                    )
                    reviews_inserted += 1

        except Exception as e:
            logger.error("Failed to inject scenario changes: %s", e)
            raise

        return ScenarioGenerateResponse(
            scenario_title=output.scenario_title,
            scenario_summary=output.scenario_summary,
            business_rationale=output.business_rationale,
            suggested_workbench_question=output.suggested_workbench_question,
            impact=ScenarioImpactSummary(
                orders_inserted=orders_inserted,
                order_items_inserted=order_items_inserted,
                inventory_updated=inventory_updated,
                reviews_inserted=reviews_inserted,
            ),
        )

    def reset_to_baseline(self) -> ScenarioResetResponse:
        """Reset the e-commerce database back to the deterministic golden seed."""
        if not self._settings.database_migrator_url:
            return ScenarioResetResponse(
                message="DATABASE_MIGRATOR_URL not configured; simulation reset skipped.",
                baseline_counts={},
            )

        counts = seed_database(
            self._settings.database_migrator_url.get_secret_value(),
            force=True,
        )
        clear_schema_cache()
        return ScenarioResetResponse(
            message="Database successfully reset to deterministic golden baseline.",
            baseline_counts=counts,
        )
