from typing import Literal

from pydantic import BaseModel, Field


class SimulatedOrderItem(BaseModel):
    product_id: int = Field(ge=1, description="Valid product ID from ecommerce.products")
    quantity: int = Field(ge=1, le=50, description="Quantity ordered")
    unit_price: float = Field(ge=0.01, le=10000.0, description="Unit price for this item")


class SimulatedOrder(BaseModel):
    customer_id: int = Field(ge=1, description="Valid customer ID from ecommerce.customers")
    status: Literal["pending", "processing", "shipped", "delivered", "cancelled"] = Field(
        default="delivered"
    )
    order_date_iso: str = Field(
        description="ISO 8601 date string for the order, e.g. 2026-03-15T14:30:00Z"
    )
    items: list[SimulatedOrderItem] = Field(
        default_factory=list, min_length=1, max_length=10, description="Order items"
    )


class SimulatedInventoryAdjustment(BaseModel):
    product_id: int = Field(ge=1, description="Product ID to adjust inventory for")
    warehouse: str = Field(description="Warehouse code, e.g. WH-EAST, WH-WEST, WH-CENTRAL")
    quantity_delta: int = Field(
        description="Quantity change (negative to simulate stock depletion, positive for restock)"
    )


class SimulatedReview(BaseModel):
    product_id: int = Field(ge=1, description="Product reviewed")
    customer_id: int = Field(ge=1, description="Customer submitting review")
    rating: int = Field(ge=1, le=5, description="Star rating (1-5)")
    title: str = Field(max_length=200, description="Review headline")
    comment: str = Field(description="Review feedback body")


class ScenarioGenerationOutput(BaseModel):
    """Structured output synthesized by the AI Scenario Generator."""

    scenario_title: str = Field(description="Short, impactful business title for the scenario")
    scenario_summary: str = Field(description="Executive summary of the simulated event")
    business_rationale: str = Field(description="Underlying market forces or testing intention")
    suggested_workbench_question: str = Field(
        description="A relevant natural language question to investigate this scenario in Workbench"
    )
    simulated_orders: list[SimulatedOrder] = Field(default_factory=list)
    inventory_adjustments: list[SimulatedInventoryAdjustment] = Field(default_factory=list)
    simulated_reviews: list[SimulatedReview] = Field(default_factory=list)


class ScenarioGenerateRequest(BaseModel):
    scenario_prompt: str = Field(
        min_length=5,
        max_length=1500,
        description="Natural language description of the business scenario to simulate.",
    )
    connection_id: str | None = Field(default=None)


class ScenarioImpactSummary(BaseModel):
    orders_inserted: int = 0
    order_items_inserted: int = 0
    inventory_updated: int = 0
    reviews_inserted: int = 0


class ScenarioGenerateResponse(BaseModel):
    scenario_title: str
    scenario_summary: str
    business_rationale: str
    suggested_workbench_question: str
    impact: ScenarioImpactSummary


class ScenarioResetResponse(BaseModel):
    status: Literal["reset_complete"] = "reset_complete"
    message: str
    baseline_counts: dict[str, int]
