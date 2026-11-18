from uuid import uuid4

import psycopg
import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import load_settings, to_psycopg_dsn
from app.main import create_app
from app.modules.database.seed import seed_database

EXPECTED_ECOMMERCE_TABLES = {
    "addresses",
    "categories",
    "customers",
    "inventory",
    "order_items",
    "orders",
    "payments",
    "reviews",
    "products",
}


@pytest.mark.integration
def test_ecommerce_tables_seeded_and_mathematically_consistent() -> None:
    settings = load_settings()
    ro_dsn = to_psycopg_dsn(settings.database_ro_url.get_secret_value())

    with psycopg.connect(ro_dsn, connect_timeout=5) as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM ecommerce.categories")
        assert cur.fetchone() == (15,)

        cur.execute("SELECT COUNT(*) FROM ecommerce.customers")
        assert cur.fetchone() == (1200,)

        cur.execute("SELECT COUNT(*) FROM ecommerce.products")
        assert cur.fetchone() == (200,)

        cur.execute("SELECT COUNT(*) FROM ecommerce.inventory")
        assert cur.fetchone() == (200,)

        cur.execute("SELECT COUNT(*) FROM ecommerce.orders")
        assert cur.fetchone() == (12000,)

        cur.execute("SELECT COUNT(*) FROM ecommerce.reviews")
        assert cur.fetchone() == (4500,)

        # Verify order total integrity across all 12,000 orders.
        cur.execute(
            """
            SELECT COUNT(*)
            FROM ecommerce.orders
            WHERE total_amount <> (subtotal_amount - discount_amount + shipping_amount)
            """
        )
        assert cur.fetchone() == (0,)


@pytest.mark.integration
def test_ro_role_table_level_isolation_and_write_rejection() -> None:
    settings = load_settings()
    ro_dsn = to_psycopg_dsn(settings.database_ro_url.get_secret_value())

    with psycopg.connect(ro_dsn, connect_timeout=5) as conn, conn.cursor() as cur:
        # Read-only account can read every ecommerce table.
        for table in sorted(EXPECTED_ECOMMERCE_TABLES):
            cur.execute(f"SELECT COUNT(*) FROM ecommerce.{table}")
            row = cur.fetchone()
            assert row is not None and row[0] > 0

        # Read-only account cannot write to ecommerce tables.
        with pytest.raises(psycopg.errors.ReadOnlySqlTransaction):
            cur.execute(
                """
                INSERT INTO ecommerce.customers (email, full_name, segment, country_code)
                VALUES ('blocked@example.test', 'Blocked User', 'retail', 'US')
                """
            )
        conn.rollback()

        with pytest.raises(psycopg.errors.ReadOnlySqlTransaction):
            cur.execute("DELETE FROM ecommerce.reviews WHERE id = 1")
        conn.rollback()

        # Read-only account cannot read app_meta telemetry or alembic_version.
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            cur.execute("SELECT COUNT(*) FROM app_meta.query_runs")
        conn.rollback()

        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            cur.execute("SELECT version_num FROM app_meta.alembic_version")
        conn.rollback()


@pytest.mark.integration
def test_app_role_scoped_to_query_runs_only() -> None:
    settings = load_settings()
    app_dsn = to_psycopg_dsn(settings.database_app_url.get_secret_value())

    with psycopg.connect(app_dsn, connect_timeout=5) as conn, conn.cursor() as cur:
        # Telemetry account can INSERT, SELECT, and UPDATE on app_meta.query_runs.
        run_id = uuid4()
        cur.execute(
            """
            INSERT INTO app_meta.query_runs (
                id, connection_id, actor_id, mode, security_status, execution_status
            )
            VALUES (%s, 'ecommerce_demo', 'local-dev', 'manual_sql', 'passed', 'success')
            """,
            (run_id,),
        )
        cur.execute(
            "UPDATE app_meta.query_runs SET row_count = 10 WHERE id = %s",
            (run_id,),
        )
        cur.execute(
            "SELECT row_count FROM app_meta.query_runs WHERE id = %s",
            (run_id,),
        )
        assert cur.fetchone() == (10,)
        conn.rollback()

        # Telemetry account cannot DELETE from app_meta.query_runs.
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            cur.execute("DELETE FROM app_meta.query_runs")
        conn.rollback()

        # Telemetry account cannot access Alembic's version table.
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            cur.execute("SELECT version_num FROM app_meta.alembic_version")
        conn.rollback()

        # Telemetry account cannot access ecommerce business tables.
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            cur.execute("SELECT COUNT(*) FROM ecommerce.customers")
        conn.rollback()


@pytest.mark.integration
async def test_live_schema_endpoint_returns_only_ecommerce_metadata() -> None:
    settings = load_settings()
    app = create_app(settings=settings)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/v1/schema")

    assert response.status_code == 200
    payload = response.json()
    assert payload["connection_id"] == "ecommerce_demo"
    assert payload["read_only"] is True
    assert payload["schemas"] == ["ecommerce"]
    assert payload["table_count"] == 9

    returned_tables = {table["table_name"]: table for table in payload["tables"]}
    assert set(returned_tables.keys()) == EXPECTED_ECOMMERCE_TABLES

    orders_meta = returned_tables["orders"]
    assert orders_meta["estimated_row_count"] > 0
    assert orders_meta["total_size_bytes"] > 0
    assert orders_meta["primary_key_columns"] == ["id"]
    assert any(
        fk["column_name"] == "customer_id" and fk["referenced_table"] == "customers"
        for fk in orders_meta["foreign_keys"]
    )
    assert any(idx["name"] == "ix_orders_customer_id" for idx in orders_meta["indexes"])

    # Never leak app_meta tables or any secret credential values.
    assert "app_meta" not in response.text
    assert "query_runs" not in response.text
    assert "alembic_version" not in response.text
    assert settings.database_ro_url.get_secret_value() not in response.text


@pytest.mark.integration
def test_seed_is_idempotent_and_reproducible() -> None:
    settings = load_settings()
    assert settings.database_migrator_url is not None
    migrator_url = settings.database_migrator_url.get_secret_value()

    first_counts = seed_database(migrator_url, seed=42, force=False)
    second_counts = seed_database(migrator_url, seed=42, force=True)
    assert first_counts == second_counts
