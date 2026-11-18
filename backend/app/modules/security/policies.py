from sqlglot import exp

MAX_SQL_LENGTH = 20_000

# Strict root-node allowlist: only read-only SELECT and set operations over SELECTs.
ALLOWED_ROOT_EXPRESSION_TYPES: tuple[type[exp.Expression], ...] = (
    exp.Select,
    exp.Union,
    exp.Intersect,
    exp.Except,
)

# Forbidden AST nodes rejected anywhere in the query tree (including CTEs and subqueries).
FORBIDDEN_AST_EXPRESSION_TYPES: tuple[type[exp.Expression], ...] = (
    exp.Alter,
    exp.Command,
    exp.Commit,
    exp.Copy,
    exp.Create,
    exp.Delete,
    exp.Drop,
    exp.Grant,
    exp.Insert,
    exp.Into,
    exp.Kill,
    exp.LoadData,
    exp.Lock,
    exp.Merge,
    exp.Pragma,
    exp.Revoke,
    exp.Rollback,
    exp.Set,
    exp.Transaction,
    exp.TruncateTable,
    exp.Update,
)

# Dangerous PostgreSQL functions blocked whether bare or schema-qualified.
BLOCKED_FUNCTION_NAMES: frozenset[str] = frozenset(
    {
        "current_setting",
        "database_to_xml",
        "database_to_xml_and_xmlschema",
        "dblink",
        "nextval",
        "query_to_xml",
        "query_to_xml_and_xmlschema",
        "schema_to_xml",
        "set_config",
        "setval",
        "table_to_xml",
        "table_to_xml_and_xmlschema",
    }
)

# Block all PostgreSQL internal/admin/network/transaction-ID/large-object function families.
BLOCKED_FUNCTION_PREFIXES: tuple[str, ...] = (
    "dblink_",
    "inet_",
    "lo_",
    "pg_",
    "txid_",
)

# Internal application tables blocked even when referenced without a schema prefix.
BLOCKED_UNQUALIFIED_TABLES: frozenset[str] = frozenset(
    {
        "alembic_version",
        "query_runs",
    }
)

# Block all unqualified PostgreSQL system catalog tables/views (resolved implicitly via pg_catalog).
BLOCKED_UNQUALIFIED_TABLE_PREFIXES: tuple[str, ...] = ("pg_",)
