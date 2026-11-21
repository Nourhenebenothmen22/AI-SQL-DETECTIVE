import time
from unittest.mock import MagicMock

import pytest
from pydantic import SecretStr

from app.modules.connections.registry import DatabaseConnectionSpec
from app.modules.database.introspector import (
    clear_schema_cache,
    introspect_schema,
)
from app.schemas.schema import (
    ColumnMetadata,
    SchemaIntrospectionResponse,
    TableMetadata,
)


def _mock_spec(conn_id: str = "test_conn") -> DatabaseConnectionSpec:
    return DatabaseConnectionSpec(
        id=conn_id,
        display_name="Test",
        description="",
        dsn=SecretStr("postgresql+psycopg://user:pw@host:5432/db"),
        target_schemas=("ecommerce",),
        read_only=True,
        max_rows=100,
        statement_timeout_ms=5000,
    )


def _mock_schema(conn_id: str) -> SchemaIntrospectionResponse:
    return SchemaIntrospectionResponse(
        connection_id=conn_id,
        schemas=["ecommerce"],
        table_count=1,
        tables=[
            TableMetadata(
                schema_name="ecommerce",
                table_name="products",
                estimated_row_count=100,
                total_size_bytes=1024,
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


def test_schema_cache_hit_and_force_refresh(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_schema_cache()
    spec = _mock_spec("conn_cache_test")
    call_count = 0

    def _fake_connect(*_args, **_kwargs):
        nonlocal call_count
        call_count += 1
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur
        mock_conn.__enter__.return_value = mock_conn
        # Return minimal rows for tables, columns, pks, fks, indexes
        mock_cur.fetchall.side_effect = [
            [
                {
                    "schema_name": "ecommerce",
                    "table_name": "products",
                    "estimated_row_count": 50,
                    "total_size_bytes": 100,
                }
            ],
            [
                {
                    "schema_name": "ecommerce",
                    "table_name": "products",
                    "column_name": "id",
                    "data_type": "bigint",
                    "udt_name": "int8",
                    "is_nullable": "NO",
                    "default_value": None,
                }
            ],
            [{"schema_name": "ecommerce", "table_name": "products", "column_name": "id"}],
            [],
            [],
        ]
        return mock_conn

    monkeypatch.setattr("psycopg.connect", _fake_connect)

    # Call 1: Cache miss -> queries DB
    s1 = introspect_schema(spec)
    assert s1.connection_id == "conn_cache_test"
    assert s1.table_count == 1
    assert call_count == 1

    # Call 2: Cache hit -> returns cached without querying DB
    s2 = introspect_schema(spec)
    assert s2 == s1
    assert call_count == 1  # Still 1!

    # Call 3: Force refresh -> queries DB again
    s3 = introspect_schema(spec, force_refresh=True)
    assert s3 == s1
    assert call_count == 2


def test_schema_cache_ttl_and_clear(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_schema_cache()
    spec = _mock_spec("conn_ttl_test")
    call_count = 0

    def _fake_connect(*_args, **_kwargs):
        nonlocal call_count
        call_count += 1
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur
        mock_conn.__enter__.return_value = mock_conn
        mock_cur.fetchall.side_effect = [
            [
                {
                    "schema_name": "ecommerce",
                    "table_name": "orders",
                    "estimated_row_count": 10,
                    "total_size_bytes": 50,
                }
            ],
            [
                {
                    "schema_name": "ecommerce",
                    "table_name": "orders",
                    "column_name": "id",
                    "data_type": "bigint",
                    "udt_name": "int8",
                    "is_nullable": "NO",
                    "default_value": None,
                }
            ],
            [],
            [],
            [],
        ]
        return mock_conn

    monkeypatch.setattr("psycopg.connect", _fake_connect)

    # Cache with very short TTL
    introspect_schema(spec, cache_ttl_seconds=0.01)
    assert call_count == 1

    time.sleep(0.02)
    # TTL elapsed -> should query again
    introspect_schema(spec)
    assert call_count == 2

    # Clear cache explicitly
    clear_schema_cache(spec.id)
    introspect_schema(spec)
    assert call_count == 3
