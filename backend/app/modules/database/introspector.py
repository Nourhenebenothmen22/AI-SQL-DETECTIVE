import threading
import time
from dataclasses import dataclass

import psycopg
from psycopg.rows import dict_row

from app.core.config import to_psycopg_dsn
from app.modules.connections.registry import DatabaseConnectionSpec
from app.schemas.schema import (
    ColumnMetadata,
    ForeignKeyMetadata,
    IndexMetadata,
    SchemaIntrospectionResponse,
    TableMetadata,
)

TABLES_QUERY = """
SELECT
    n.nspname AS schema_name,
    c.relname AS table_name,
    GREATEST(COALESCE(s.n_live_tup, c.reltuples, 0), 0)::bigint AS estimated_row_count,
    pg_total_relation_size(c.oid)::bigint AS total_size_bytes
FROM pg_catalog.pg_class c
JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
LEFT JOIN pg_catalog.pg_stat_user_tables s ON s.relid = c.oid
WHERE c.relkind IN ('r', 'p')
  AND n.nspname = ANY(%s)
ORDER BY n.nspname, c.relname;
"""

COLUMNS_QUERY = """
SELECT
    table_schema AS schema_name,
    table_name,
    column_name,
    data_type,
    udt_name,
    (is_nullable = 'YES') AS is_nullable,
    column_default AS default_value
FROM information_schema.columns
WHERE table_schema = ANY(%s)
ORDER BY table_schema, table_name, ordinal_position;
"""

PRIMARY_KEYS_QUERY = """
SELECT
    n.nspname AS schema_name,
    c.relname AS table_name,
    a.attname AS column_name
FROM pg_catalog.pg_constraint con
JOIN pg_catalog.pg_class c ON c.oid = con.conrelid
JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
JOIN LATERAL unnest(con.conkey) WITH ORDINALITY AS cols(attnum, ord) ON true
JOIN pg_catalog.pg_attribute a ON a.attrelid = c.oid AND a.attnum = cols.attnum
WHERE con.contype = 'p'
  AND n.nspname = ANY(%s)
ORDER BY n.nspname, c.relname, cols.ord;
"""

FOREIGN_KEYS_QUERY = """
SELECT
    n.nspname AS schema_name,
    c.relname AS table_name,
    con.conname AS constraint_name,
    a.attname AS column_name,
    rn.nspname AS referenced_schema,
    rc.relname AS referenced_table,
    ra.attname AS referenced_column
FROM pg_catalog.pg_constraint con
JOIN pg_catalog.pg_class c ON c.oid = con.conrelid
JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
JOIN pg_catalog.pg_class rc ON rc.oid = con.confrelid
JOIN pg_catalog.pg_namespace rn ON rn.oid = rc.relnamespace
JOIN LATERAL unnest(con.conkey, con.confkey) WITH ORDINALITY
    AS cols(attnum, ref_attnum, ord) ON true
JOIN pg_catalog.pg_attribute a ON a.attrelid = c.oid AND a.attnum = cols.attnum
JOIN pg_catalog.pg_attribute ra ON ra.attrelid = rc.oid AND ra.attnum = cols.ref_attnum
WHERE con.contype = 'f'
  AND n.nspname = ANY(%s)
ORDER BY n.nspname, c.relname, con.conname, cols.ord;
"""

INDEXES_QUERY = """
SELECT
    n.nspname AS schema_name,
    t.relname AS table_name,
    i.relname AS index_name,
    ix.indisunique AS is_unique,
    ix.indisprimary AS is_primary,
    am.amname AS index_type,
    ARRAY(
        SELECT pg_catalog.pg_get_indexdef(ix.indexrelid, k + 1, true)
        FROM generate_subscripts(ix.indkey, 1) AS k
        ORDER BY k
    ) AS columns
FROM pg_catalog.pg_index ix
JOIN pg_catalog.pg_class t ON t.oid = ix.indrelid
JOIN pg_catalog.pg_class i ON i.oid = ix.indexrelid
JOIN pg_catalog.pg_namespace n ON n.oid = t.relnamespace
JOIN pg_catalog.pg_am am ON am.oid = i.relam
WHERE n.nspname = ANY(%s)
ORDER BY n.nspname, t.relname, i.relname;
"""


@dataclass(frozen=True, slots=True)
class _SchemaCacheEntry:
    response: SchemaIntrospectionResponse
    expires_at: float


_SCHEMA_CACHE: dict[str, _SchemaCacheEntry] = {}
_SCHEMA_CACHE_LOCK = threading.Lock()
DEFAULT_SCHEMA_CACHE_TTL_SECONDS: float = 600.0  # 10 minutes


def clear_schema_cache(connection_id: str | None = None) -> None:
    """Clear cached schema introspection metadata."""
    with _SCHEMA_CACHE_LOCK:
        if connection_id is not None:
            prefix = f"{connection_id}::"
            keys_to_remove = [
                k for k in _SCHEMA_CACHE if k.startswith(prefix) or k == connection_id
            ]
            for k in keys_to_remove:
                del _SCHEMA_CACHE[k]
        else:
            _SCHEMA_CACHE.clear()


def introspect_schema(
    spec: DatabaseConnectionSpec,
    *,
    force_refresh: bool = False,
    cache_ttl_seconds: float = DEFAULT_SCHEMA_CACHE_TTL_SECONDS,
) -> SchemaIntrospectionResponse:
    """Introspect target schemas via read-only PostgreSQL connection with in-memory caching."""
    schemas = list(spec.target_schemas)
    cache_key = f"{spec.id}::{','.join(sorted(schemas))}"

    if not force_refresh:
        now = time.monotonic()
        with _SCHEMA_CACHE_LOCK:
            entry = _SCHEMA_CACHE.get(cache_key)
            if entry is not None and now < entry.expires_at:
                return entry.response

    dsn = to_psycopg_dsn(spec.dsn.get_secret_value())

    with psycopg.connect(dsn, connect_timeout=5, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute("BEGIN TRANSACTION READ ONLY")
            cur.execute(
                "SELECT set_config('statement_timeout', %s, true)",
                (f"{spec.statement_timeout_ms}ms",),
            )
            cur.execute("SELECT set_config('lock_timeout', '1000ms', true)")

            cur.execute(TABLES_QUERY, (schemas,))
            table_rows = cur.fetchall()

            cur.execute(COLUMNS_QUERY, (schemas,))
            column_rows = cur.fetchall()

            cur.execute(PRIMARY_KEYS_QUERY, (schemas,))
            pk_rows = cur.fetchall()

            cur.execute(FOREIGN_KEYS_QUERY, (schemas,))
            fk_rows = cur.fetchall()

            cur.execute(INDEXES_QUERY, (schemas,))
            index_rows = cur.fetchall()

        conn.rollback()

    pks_by_table: dict[tuple[str, str], list[str]] = {}
    for row in pk_rows:
        key = (row["schema_name"], row["table_name"])
        pks_by_table.setdefault(key, []).append(row["column_name"])

    fks_by_table: dict[tuple[str, str], list[ForeignKeyMetadata]] = {}
    fk_targets_by_col: dict[tuple[str, str, str], str] = {}
    for row in fk_rows:
        key = (row["schema_name"], row["table_name"])
        fk = ForeignKeyMetadata(
            constraint_name=row["constraint_name"],
            column_name=row["column_name"],
            referenced_schema=row["referenced_schema"],
            referenced_table=row["referenced_table"],
            referenced_column=row["referenced_column"],
        )
        fks_by_table.setdefault(key, []).append(fk)
        fk_targets_by_col[(row["schema_name"], row["table_name"], row["column_name"])] = (
            f"{fk.referenced_schema}.{fk.referenced_table}.{fk.referenced_column}"
        )

    columns_by_table: dict[tuple[str, str], list[ColumnMetadata]] = {}
    for row in column_rows:
        key = (row["schema_name"], row["table_name"])
        col_name = row["column_name"]
        pk_cols = pks_by_table.get(key, [])
        fk_target = fk_targets_by_col.get((row["schema_name"], row["table_name"], col_name))
        columns_by_table.setdefault(key, []).append(
            ColumnMetadata(
                name=col_name,
                data_type=row["data_type"],
                udt_name=row["udt_name"],
                is_nullable=bool(row["is_nullable"]),
                default_value=row["default_value"],
                is_primary_key=col_name in pk_cols,
                is_foreign_key=fk_target is not None,
                foreign_key_target=fk_target,
            )
        )

    indexes_by_table: dict[tuple[str, str], list[IndexMetadata]] = {}
    for row in index_rows:
        key = (row["schema_name"], row["table_name"])
        indexes_by_table.setdefault(key, []).append(
            IndexMetadata(
                name=row["index_name"],
                columns=list(row["columns"] or []),
                is_unique=bool(row["is_unique"]),
                is_primary=bool(row["is_primary"]),
                index_type=row["index_type"],
            )
        )

    tables = [
        TableMetadata(
            schema_name=row["schema_name"],
            table_name=row["table_name"],
            estimated_row_count=int(row["estimated_row_count"]),
            total_size_bytes=int(row["total_size_bytes"]),
            columns=columns_by_table.get((row["schema_name"], row["table_name"]), []),
            primary_key_columns=pks_by_table.get((row["schema_name"], row["table_name"]), []),
            foreign_keys=fks_by_table.get((row["schema_name"], row["table_name"]), []),
            indexes=indexes_by_table.get((row["schema_name"], row["table_name"]), []),
        )
        for row in table_rows
    ]

    response = SchemaIntrospectionResponse(
        connection_id=spec.id,
        dialect="postgresql",
        read_only=spec.read_only,
        schemas=schemas,
        table_count=len(tables),
        tables=tables,
    )

    with _SCHEMA_CACHE_LOCK:
        _SCHEMA_CACHE[cache_key] = _SchemaCacheEntry(
            response=response,
            expires_at=time.monotonic() + max(0.001, cache_ttl_seconds),
        )

    return response


def format_compact_schema_prompt(schema: SchemaIntrospectionResponse) -> str:
    """Render a compact, grounded schema summary for downstream AI schema analysis."""
    lines: list[str] = []
    for table in schema.tables:
        col_parts: list[str] = []
        for col in table.columns:
            tags: list[str] = []
            if col.is_primary_key:
                tags.append("PK")
            if col.foreign_key_target:
                tags.append(f"FK->{col.foreign_key_target}")
            if not col.is_nullable:
                tags.append("NOT NULL")
            suffix = f" [{', '.join(tags)}]" if tags else ""
            col_parts.append(f"{col.name}:{col.udt_name}{suffix}")
        idx_names = ", ".join(
            f"{idx.name}({','.join(idx.columns)})" for idx in table.indexes if not idx.is_primary
        )
        idx_suffix = f" | indexes: {idx_names}" if idx_names else ""
        lines.append(
            f"{table.schema_name}.{table.table_name} (~{table.estimated_row_count} rows): "
            f"{', '.join(col_parts)}{idx_suffix}"
        )
    return "\n".join(lines)
