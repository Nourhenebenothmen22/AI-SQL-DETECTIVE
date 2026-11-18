import psycopg
import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import load_settings, to_psycopg_dsn
from app.main import create_app


@pytest.mark.integration
def test_readonly_role_isolation_and_write_protection() -> None:
    settings = load_settings()
    ro_dsn = to_psycopg_dsn(settings.database_ro_url.get_secret_value())
    with psycopg.connect(ro_dsn, connect_timeout=3) as conn, conn.cursor() as cur:
        cur.execute("SHOW default_transaction_read_only")
        assert cur.fetchone() == ("on",)

        cur.execute("SELECT has_schema_privilege(current_user, 'ecommerce', 'USAGE')")
        assert cur.fetchone() == (True,)

        cur.execute("SELECT has_schema_privilege(current_user, 'app_meta', 'USAGE')")
        assert cur.fetchone() == (False,)

        cur.execute("SELECT has_schema_privilege(current_user, 'public', 'CREATE')")
        assert cur.fetchone() == (False,)

        with pytest.raises(psycopg.errors.ReadOnlySqlTransaction):
            cur.execute("CREATE TEMP TABLE should_fail (id int)")
        conn.rollback()


@pytest.mark.integration
def test_app_telemetry_role_isolation() -> None:
    settings = load_settings()
    app_dsn = to_psycopg_dsn(settings.database_app_url.get_secret_value())
    with psycopg.connect(app_dsn, connect_timeout=3) as conn, conn.cursor() as cur:
        cur.execute("SELECT has_schema_privilege(current_user, 'app_meta', 'USAGE')")
        assert cur.fetchone() == (True,)

        cur.execute("SELECT has_schema_privilege(current_user, 'app_meta', 'CREATE')")
        assert cur.fetchone() == (False,)

        cur.execute("SELECT has_schema_privilege(current_user, 'ecommerce', 'USAGE')")
        assert cur.fetchone() == (False,)

        cur.execute("SELECT has_schema_privilege(current_user, 'public', 'CREATE')")
        assert cur.fetchone() == (False,)


@pytest.mark.integration
async def test_health_endpoint_connects_to_live_postgres() -> None:
    settings = load_settings()
    app = create_app(settings=settings)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/v1/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["database_status"] == "connected"
