import pytest
from pydantic import SecretStr

from app.modules.connections.registry import DatabaseConnectionSpec
from app.modules.execution.executor import SQLExecutor
from app.modules.security.gate import SecurityGate
from app.modules.security.types import ValidatedSQL

ALLOWED_SCHEMAS = ("ecommerce",)

ADVERSARIAL_PAYLOADS = [
    # Destructive DDL & DML
    "DROP TABLE ecommerce.orders",
    "DELETE FROM ecommerce.orders WHERE id = 1",
    "UPDATE ecommerce.orders SET status = 'cancelled'",
    "INSERT INTO ecommerce.customers (email, full_name, country_code) VALUES ('x@y.z', 'X', 'US')",
    "TRUNCATE TABLE ecommerce.orders",
    "ALTER TABLE ecommerce.orders ADD COLUMN pwned text",
    "CREATE TABLE ecommerce.rogue (id int)",
    "GRANT ALL ON ecommerce.orders TO PUBLIC",
    "REVOKE ALL ON ecommerce.orders FROM PUBLIC",
    # Administrative / procedural / EXPLAIN ANALYZE
    "COPY ecommerce.orders TO STDOUT",
    "DO $$ BEGIN PERFORM 1; END $$;",
    "CALL some_proc()",
    "SET statement_timeout = 0",
    "EXPLAIN ANALYZE SELECT * FROM ecommerce.orders",
    # Multi-statement / stacked injection
    "SELECT 1; DROP TABLE ecommerce.orders",
    "SELECT id FROM ecommerce.orders LIMIT 1; SELECT id FROM ecommerce.customers LIMIT 1",
    # Writable CTEs
    "WITH d AS (DELETE FROM ecommerce.orders RETURNING id) SELECT * FROM d",
    "WITH u AS (UPDATE ecommerce.orders SET status = 'paid' RETURNING id) SELECT * FROM u",
    "WITH i AS (INSERT INTO ecommerce.categories (name, slug) VALUES ('X', 'x') RETURNING id) "
    "SELECT * FROM i",
    # SELECT INTO and row-level locking
    "SELECT * INTO ecommerce.stolen FROM ecommerce.orders",
    "SELECT id FROM ecommerce.orders FOR UPDATE",
    "SELECT id FROM ecommerce.orders FOR SHARE",
    # Dangerous PostgreSQL functions (bare and schema-qualified)
    "SELECT pg_sleep(5)",
    "SELECT pg_catalog.pg_sleep(5)",
    "SELECT pg_read_file('/etc/passwd')",
    "SELECT pg_catalog.pg_read_binary_file('/etc/passwd')",
    "SELECT set_config('statement_timeout', '0', false)",
    "SELECT lo_import('/etc/passwd')",
    "SELECT dblink('host=evil', 'SELECT 1')",
    "SELECT nextval('ecommerce.orders_id_seq')",
    "SELECT pg_notify('chan', 'msg')",
    "SELECT pg_current_logfile()",
    "SELECT pg_stat_get_activity(NULL)",
    "SELECT pg_backend_pid()",
    "SELECT inet_client_port()",
    "SELECT txid_current()",
    # Schema isolation escapes & restricted system tables (qualified and unqualified pg_*)
    "SELECT * FROM app_meta.query_runs",
    "SELECT * FROM app_meta.alembic_version",
    "SELECT * FROM pg_catalog.pg_authid",
    "SELECT * FROM information_schema.tables",
    "SELECT * FROM public.anything",
    "SELECT * FROM pg_shadow",
    "SELECT * FROM pg_roles",
    "SELECT * FROM pg_tables",
    "SELECT * FROM pg_class",
    "SELECT * FROM pg_stat_user_tables",
    "SELECT * FROM pg_stat_replication",
    "SELECT * FROM pg_prepared_statements",
    "SELECT * FROM query_runs",
    "SELECT * FROM alembic_version",
    "SELECT * FROM otherdb.ecommerce.orders",
    # Empty / malformed SQL
    "   ",
    "SELECT FROM WHERE ???",
]


@pytest.mark.parametrize("payload", ADVERSARIAL_PAYLOADS)
def test_security_gate_blocks_all_adversarial_payloads(payload: str) -> None:
    gate = SecurityGate()
    result = gate.validate(payload, allowed_schemas=ALLOWED_SCHEMAS, max_rows=200)

    assert result.passed is False, f"Expected payload to be blocked: {payload}"
    assert result.validated_sql is None
    assert len(result.violations) >= 1


def test_security_gate_allows_safe_queries_and_injects_limit() -> None:
    gate = SecurityGate()
    sql = (
        "WITH recent_orders AS ("
        "  SELECT customer_id, total_amount FROM ecommerce.orders WHERE status = 'delivered'"
        ") "
        "SELECT c.segment, COUNT(*) AS order_count, SUM(r.total_amount) AS revenue "
        "FROM recent_orders r "
        "JOIN ecommerce.customers c ON c.id = r.customer_id "
        "GROUP BY c.segment"
    )
    result = gate.validate(sql, allowed_schemas=ALLOWED_SCHEMAS, max_rows=200)

    assert result.passed is True
    assert result.validated_sql is not None
    assert result.validated_sql.enforced_limit == 200
    assert result.validated_sql.limit_was_injected is True
    assert result.validated_sql.limit_was_clamped is False
    assert "LIMIT 200" in result.validated_sql.normalized_sql


def test_security_gate_preserves_smaller_limit_and_clamps_excessive_limits() -> None:
    gate = SecurityGate()

    small = gate.validate(
        "SELECT id FROM ecommerce.orders LIMIT 15",
        allowed_schemas=ALLOWED_SCHEMAS,
        max_rows=200,
    )
    assert small.passed is True
    assert small.validated_sql is not None
    assert small.validated_sql.enforced_limit == 15
    assert small.validated_sql.limit_was_injected is False
    assert small.validated_sql.limit_was_clamped is False

    excessive = gate.validate(
        "SELECT id FROM ecommerce.orders LIMIT 5000",
        allowed_schemas=ALLOWED_SCHEMAS,
        max_rows=200,
    )
    assert excessive.passed is True
    assert excessive.validated_sql is not None
    assert excessive.validated_sql.enforced_limit == 200
    assert excessive.validated_sql.limit_was_clamped is True
    assert "LIMIT 200" in excessive.validated_sql.normalized_sql

    fetch_excessive = gate.validate(
        "SELECT id FROM ecommerce.orders FETCH FIRST 5000 ROWS ONLY",
        allowed_schemas=ALLOWED_SCHEMAS,
        max_rows=100,
    )
    assert fetch_excessive.passed is True
    assert fetch_excessive.validated_sql is not None
    assert fetch_excessive.validated_sql.enforced_limit == 100
    assert fetch_excessive.validated_sql.limit_was_clamped is True

    limit_all = gate.validate(
        "SELECT id FROM ecommerce.orders LIMIT ALL",
        allowed_schemas=ALLOWED_SCHEMAS,
        max_rows=150,
    )
    assert limit_all.passed is True
    assert limit_all.validated_sql is not None
    assert limit_all.validated_sql.enforced_limit == 150
    assert limit_all.validated_sql.limit_was_clamped is True


def test_security_gate_allows_union_of_safe_selects() -> None:
    gate = SecurityGate()
    sql = (
        "SELECT id FROM ecommerce.orders WHERE status = 'paid' "
        "UNION ALL "
        "SELECT id FROM ecommerce.orders WHERE status = 'shipped'"
    )
    result = gate.validate(sql, allowed_schemas=ALLOWED_SCHEMAS, max_rows=50)
    assert result.passed is True
    assert result.validated_sql is not None
    assert result.validated_sql.enforced_limit == 50


def test_security_gate_allows_trailing_comment_after_semicolon_and_detects_wildcard() -> None:
    gate = SecurityGate()

    with_comment = gate.validate(
        "SELECT id, status FROM ecommerce.orders; -- trailing editor comment",
        allowed_schemas=ALLOWED_SCHEMAS,
        max_rows=50,
    )
    assert with_comment.passed is True
    assert with_comment.validated_sql is not None
    assert with_comment.validated_sql.has_select_star is False
    assert "LIMIT 50" in with_comment.validated_sql.normalized_sql
    assert "LIMIT 51" in with_comment.validated_sql.execution_sql

    stacked_with_comment = gate.validate(
        "SELECT 1; SELECT 2 -- trailing comment",
        allowed_schemas=ALLOWED_SCHEMAS,
        max_rows=50,
    )
    assert stacked_with_comment.passed is False

    count_star = gate.validate(
        "SELECT COUNT(*) AS total FROM ecommerce.orders",
        allowed_schemas=ALLOWED_SCHEMAS,
        max_rows=50,
    )
    assert count_star.passed is True
    assert count_star.validated_sql is not None
    assert count_star.validated_sql.has_select_star is False

    alias_star = gate.validate(
        "SELECT o.* FROM ecommerce.orders o",
        allowed_schemas=ALLOWED_SCHEMAS,
        max_rows=50,
    )
    assert alias_star.passed is True
    assert alias_star.validated_sql is not None
    assert alias_star.validated_sql.has_select_star is True


def test_validated_sql_cannot_be_forged_and_executor_rejects_raw_strings() -> None:
    with pytest.raises(PermissionError):
        ValidatedSQL(
            original_sql="DROP TABLE ecommerce.orders",
            normalized_sql="DROP TABLE ecommerce.orders",
            execution_sql="DROP TABLE ecommerce.orders",
            enforced_limit=10,
            limit_was_injected=False,
            limit_was_clamped=False,
            has_select_star=False,
            checks=(),
            _token=object(),
        )

    spec = DatabaseConnectionSpec(
        id="ecommerce_demo",
        display_name="Demo",
        description="Test",
        dsn=SecretStr("postgresql+psycopg://ro:mock@localhost:5434/test"),
        target_schemas=("ecommerce",),
        statement_timeout_ms=5000,
        max_rows=200,
    )
    executor = SQLExecutor()
    with pytest.raises(TypeError, match="ValidatedSQL"):
        executor.execute("SELECT 1", spec)  # type: ignore[arg-type]
