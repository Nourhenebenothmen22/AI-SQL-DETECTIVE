"""Initial ecommerce business schema and app_meta telemetry schema.

Revision ID: 0001_initial
Revises:
Create Date: 2026-11-18 07:20:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- ecommerce schema ---
    op.create_table(
        "customers",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=160), nullable=False),
        sa.Column("segment", sa.String(length=32), server_default="retail", nullable=False),
        sa.Column("country_code", sa.String(length=2), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "segment IN ('retail', 'vip', 'wholesale')",
            name="ck_customers_segment_valid",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_customers"),
        sa.UniqueConstraint("email", name="uq_customers_email"),
        schema="ecommerce",
    )

    op.create_table(
        "addresses",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("customer_id", sa.BigInteger(), nullable=False),
        sa.Column("city", sa.String(length=120), nullable=False),
        sa.Column("state", sa.String(length=120), nullable=False),
        sa.Column("country_code", sa.String(length=2), nullable=False),
        sa.Column("is_default", sa.Boolean(), server_default="false", nullable=False),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["ecommerce.customers.id"],
            name="fk_addresses_customer_id_customers",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_addresses"),
        schema="ecommerce",
    )
    op.create_index("ix_addresses_customer_id", "addresses", ["customer_id"], schema="ecommerce")

    op.create_table(
        "categories",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("parent_id", sa.BigInteger(), nullable=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=140), nullable=False),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["ecommerce.categories.id"],
            name="fk_categories_parent_id_categories",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_categories"),
        sa.UniqueConstraint("slug", name="uq_categories_slug"),
        schema="ecommerce",
    )

    op.create_table(
        "products",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("category_id", sa.BigInteger(), nullable=False),
        sa.Column("sku", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("unit_price", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("cost_price", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("unit_price >= 0", name="ck_products_unit_price_non_negative"),
        sa.CheckConstraint("cost_price >= 0", name="ck_products_cost_price_non_negative"),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["ecommerce.categories.id"],
            name="fk_products_category_id_categories",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_products"),
        sa.UniqueConstraint("sku", name="uq_products_sku"),
        schema="ecommerce",
    )
    op.create_index("ix_products_category_id", "products", ["category_id"], schema="ecommerce")

    op.create_table(
        "inventory",
        sa.Column("product_id", sa.BigInteger(), nullable=False),
        sa.Column("stock_quantity", sa.Integer(), nullable=False),
        sa.Column("reorder_level", sa.Integer(), nullable=False),
        sa.Column("warehouse_code", sa.String(length=32), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("stock_quantity >= 0", name="ck_inventory_stock_quantity_non_negative"),
        sa.CheckConstraint("reorder_level >= 0", name="ck_inventory_reorder_level_non_negative"),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["ecommerce.products.id"],
            name="fk_inventory_product_id_products",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("product_id", name="pk_inventory"),
        schema="ecommerce",
    )

    op.create_table(
        "orders",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("customer_id", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("subtotal_amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column(
            "discount_amount",
            sa.Numeric(precision=12, scale=2),
            server_default="0.00",
            nullable=False,
        ),
        sa.Column(
            "shipping_amount",
            sa.Numeric(precision=12, scale=2),
            server_default="0.00",
            nullable=False,
        ),
        sa.Column("total_amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="USD", nullable=False),
        sa.Column(
            "placed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'paid', 'shipped', 'delivered', 'cancelled', 'refunded')",
            name="ck_orders_status_valid",
        ),
        sa.CheckConstraint("total_amount >= 0", name="ck_orders_total_amount_non_negative"),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["ecommerce.customers.id"],
            name="fk_orders_customer_id_customers",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_orders"),
        schema="ecommerce",
    )
    op.create_index("ix_orders_customer_id", "orders", ["customer_id"], schema="ecommerce")

    op.create_table(
        "order_items",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("order_id", sa.BigInteger(), nullable=False),
        sa.Column("product_id", sa.BigInteger(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("line_total", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.CheckConstraint("quantity > 0", name="ck_order_items_quantity_positive"),
        sa.CheckConstraint("unit_price >= 0", name="ck_order_items_unit_price_non_negative"),
        sa.CheckConstraint("line_total >= 0", name="ck_order_items_line_total_non_negative"),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["ecommerce.orders.id"],
            name="fk_order_items_order_id_orders",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["ecommerce.products.id"],
            name="fk_order_items_product_id_products",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_order_items"),
        schema="ecommerce",
    )
    op.create_index("ix_order_items_order_id", "order_items", ["order_id"], schema="ecommerce")
    op.create_index("ix_order_items_product_id", "order_items", ["product_id"], schema="ecommerce")

    op.create_table(
        "payments",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("order_id", sa.BigInteger(), nullable=False),
        sa.Column("payment_method", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "payment_method IN ('card', 'bank_transfer', 'wallet')",
            name="ck_payments_payment_method_valid",
        ),
        sa.CheckConstraint(
            "status IN ('authorized', 'captured', 'failed', 'refunded')",
            name="ck_payments_status_valid",
        ),
        sa.CheckConstraint("amount >= 0", name="ck_payments_amount_non_negative"),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["ecommerce.orders.id"],
            name="fk_payments_order_id_orders",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_payments"),
        schema="ecommerce",
    )
    op.create_index("ix_payments_order_id", "payments", ["order_id"], schema="ecommerce")

    op.create_table(
        "reviews",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("product_id", sa.BigInteger(), nullable=False),
        sa.Column("customer_id", sa.BigInteger(), nullable=False),
        sa.Column("rating", sa.SmallInteger(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=False),
        sa.Column("is_verified_purchase", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("rating BETWEEN 1 AND 5", name="ck_reviews_rating_range"),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["ecommerce.products.id"],
            name="fk_reviews_product_id_products",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["ecommerce.customers.id"],
            name="fk_reviews_customer_id_customers",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_reviews"),
        schema="ecommerce",
    )

    # --- app_meta schema ---
    op.create_table(
        "query_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("connection_id", sa.String(length=64), nullable=False),
        sa.Column("actor_id", sa.String(length=120), server_default="local-dev", nullable=False),
        sa.Column("mode", sa.String(length=24), nullable=False),
        sa.Column("natural_language_prompt", sa.Text(), nullable=True),
        sa.Column("generated_sql", sa.Text(), nullable=True),
        sa.Column("validated_sql", sa.Text(), nullable=True),
        sa.Column("security_status", sa.String(length=24), nullable=False),
        sa.Column(
            "security_violations_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("review_status", sa.String(length=32), nullable=True),
        sa.Column("execution_status", sa.String(length=24), nullable=False),
        sa.Column("execution_time_ms", sa.Float(), nullable=True),
        sa.Column("row_count", sa.Integer(), nullable=True),
        sa.Column("was_truncated", sa.Boolean(), server_default="false", nullable=False),
        sa.Column(
            "explain_plan_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("explanation_text", sa.Text(), nullable=True),
        sa.Column(
            "optimizations_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("langsmith_run_id", sa.String(length=128), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("mode IN ('nl', 'manual_sql')", name="ck_query_runs_mode_valid"),
        sa.CheckConstraint(
            "security_status IN ('passed', 'blocked')",
            name="ck_query_runs_security_status_valid",
        ),
        sa.CheckConstraint(
            "execution_status IN ('success', 'error', 'timeout', 'skipped')",
            name="ck_query_runs_execution_status_valid",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_query_runs"),
        schema="app_meta",
    )
    op.create_index("ix_query_runs_created_at", "query_runs", ["created_at"], schema="app_meta")
    op.create_index(
        "ix_query_runs_connection_id_created_at",
        "query_runs",
        ["connection_id", "created_at"],
        schema="app_meta",
    )

    # Ensure no non-owner role (such as the telemetry app role) can access Alembic's
    # version tracking table, even if PG_APP_USER is customized via environment variables.
    op.execute(
        sa.text(
            """
            DO $$
            DECLARE
                grant_row RECORD;
            BEGIN
                FOR grant_row IN
                    SELECT DISTINCT grantee
                    FROM information_schema.role_table_grants
                    WHERE table_schema = 'app_meta'
                      AND table_name = 'alembic_version'
                      AND grantee <> current_user
                LOOP
                    EXECUTE format(
                        'REVOKE ALL ON TABLE app_meta.alembic_version FROM %I',
                        grant_row.grantee
                    );
                END LOOP;
            END
            $$;
            """
        )
    )


def downgrade() -> None:
    op.drop_index(
        "ix_query_runs_connection_id_created_at",
        table_name="query_runs",
        schema="app_meta",
    )
    op.drop_index("ix_query_runs_created_at", table_name="query_runs", schema="app_meta")
    op.drop_table("query_runs", schema="app_meta")

    op.drop_table("reviews", schema="ecommerce")
    op.drop_index("ix_payments_order_id", table_name="payments", schema="ecommerce")
    op.drop_table("payments", schema="ecommerce")
    op.drop_index("ix_order_items_product_id", table_name="order_items", schema="ecommerce")
    op.drop_index("ix_order_items_order_id", table_name="order_items", schema="ecommerce")
    op.drop_table("order_items", schema="ecommerce")
    op.drop_index("ix_orders_customer_id", table_name="orders", schema="ecommerce")
    op.drop_table("orders", schema="ecommerce")
    op.drop_table("inventory", schema="ecommerce")
    op.drop_index("ix_products_category_id", table_name="products", schema="ecommerce")
    op.drop_table("products", schema="ecommerce")
    op.drop_table("categories", schema="ecommerce")
    op.drop_index("ix_addresses_customer_id", table_name="addresses", schema="ecommerce")
    op.drop_table("addresses", schema="ecommerce")
    op.drop_table("customers", schema="ecommerce")
