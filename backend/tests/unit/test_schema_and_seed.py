from decimal import Decimal

import pytest
from httpx import AsyncClient

from app.modules.database.introspector import format_compact_schema_prompt
from app.modules.database.seed import SeedScale, generate_synthetic_dataset
from app.schemas.schema import (
    ColumnMetadata,
    ForeignKeyMetadata,
    IndexMetadata,
    SchemaIntrospectionResponse,
    TableMetadata,
)


def test_synthetic_dataset_is_deterministic() -> None:
    scale = SeedScale(customers=40, products=20, orders=100, reviews=30)
    first = generate_synthetic_dataset(seed=42, scale=scale)
    second = generate_synthetic_dataset(seed=42, scale=scale)

    assert first == second
    assert len(first.categories) == 15
    assert len(first.customers) == 40
    assert len(first.products) == 20
    assert len(first.inventory) == 20
    assert len(first.orders) == 100
    assert len(first.reviews) == 30


def test_synthetic_dataset_order_math_and_referential_integrity() -> None:
    scale = SeedScale(customers=30, products=15, orders=80, reviews=25)
    dataset = generate_synthetic_dataset(seed=42, scale=scale)

    customer_ids = {row["id"] for row in dataset.customers}
    product_ids = {row["id"] for row in dataset.products}
    category_ids = {row["id"] for row in dataset.categories}

    assert all(row["category_id"] in category_ids for row in dataset.products)
    assert all(row["product_id"] in product_ids for row in dataset.inventory)
    assert all(row["customer_id"] in customer_ids for row in dataset.orders)

    subtotals_by_order: dict[int, Decimal] = {}
    for item in dataset.order_items:
        assert item["product_id"] in product_ids
        assert item["line_total"] == (item["unit_price"] * item["quantity"]).quantize(
            Decimal("0.01")
        )
        subtotals_by_order[item["order_id"]] = (
            subtotals_by_order.get(item["order_id"], Decimal("0.00")) + item["line_total"]
        )

    for order in dataset.orders:
        expected_subtotal = subtotals_by_order[order["id"]]
        assert order["subtotal_amount"] == expected_subtotal
        expected_total = (
            order["subtotal_amount"] - order["discount_amount"] + order["shipping_amount"]
        ).quantize(Decimal("0.01"))
        assert order["total_amount"] == expected_total


def test_format_compact_schema_prompt() -> None:
    schema = SchemaIntrospectionResponse(
        connection_id="ecommerce_demo",
        schemas=["ecommerce"],
        table_count=1,
        tables=[
            TableMetadata(
                schema_name="ecommerce",
                table_name="orders",
                estimated_row_count=12000,
                total_size_bytes=102400,
                columns=[
                    ColumnMetadata(
                        name="id",
                        data_type="bigint",
                        udt_name="int8",
                        is_nullable=False,
                        is_primary_key=True,
                    ),
                    ColumnMetadata(
                        name="customer_id",
                        data_type="bigint",
                        udt_name="int8",
                        is_nullable=False,
                        is_foreign_key=True,
                        foreign_key_target="ecommerce.customers.id",
                    ),
                ],
                primary_key_columns=["id"],
                foreign_keys=[
                    ForeignKeyMetadata(
                        constraint_name="fk_orders_customer_id_customers",
                        column_name="customer_id",
                        referenced_schema="ecommerce",
                        referenced_table="customers",
                        referenced_column="id",
                    )
                ],
                indexes=[
                    IndexMetadata(
                        name="ix_orders_customer_id",
                        columns=["customer_id"],
                        is_unique=False,
                        is_primary=False,
                        index_type="btree",
                    )
                ],
            )
        ],
    )

    rendered = format_compact_schema_prompt(schema)
    assert "ecommerce.orders (~12000 rows)" in rendered
    assert "id:int8 [PK, NOT NULL]" in rendered
    assert "customer_id:int8 [FK->ecommerce.customers.id, NOT NULL]" in rendered
    assert "indexes: ix_orders_customer_id(customer_id)" in rendered


async def test_schema_endpoint_returns_404_for_unknown_connection(
    async_client: AsyncClient,
) -> None:
    response = await async_client.get("/api/v1/schema", params={"connection_id": "nonexistent"})
    assert response.status_code == 404
    assert "Unknown connection_id" in response.json()["detail"]


async def test_schema_endpoint_returns_sanitized_metadata_without_credentials(
    async_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock_schema = SchemaIntrospectionResponse(
        connection_id="ecommerce_demo",
        schemas=["ecommerce"],
        table_count=1,
        tables=[
            TableMetadata(
                schema_name="ecommerce",
                table_name="customers",
                estimated_row_count=1200,
                total_size_bytes=65536,
                columns=[
                    ColumnMetadata(
                        name="id",
                        data_type="bigint",
                        udt_name="int8",
                        is_nullable=False,
                        is_primary_key=True,
                    )
                ],
                primary_key_columns=["id"],
                foreign_keys=[],
                indexes=[],
            )
        ],
    )
    monkeypatch.setattr("app.api.v1.schema.introspect_schema", lambda _spec: mock_schema)

    response = await async_client.get("/api/v1/schema")
    assert response.status_code == 200
    payload = response.json()
    assert payload["connection_id"] == "ecommerce_demo"
    assert payload["table_count"] == 1
    assert payload["tables"][0]["table_name"] == "customers"
    assert "mock_ro_secret" not in response.text
    assert "db.internal" not in response.text
