from typing import Literal

from pydantic import BaseModel


class ColumnMetadata(BaseModel):
    """Metadata for a single PostgreSQL table column."""

    name: str
    data_type: str
    udt_name: str
    is_nullable: bool
    default_value: str | None = None
    is_primary_key: bool = False
    is_foreign_key: bool = False
    foreign_key_target: str | None = None


class ForeignKeyMetadata(BaseModel):
    """Metadata for a foreign key constraint."""

    constraint_name: str
    column_name: str
    referenced_schema: str
    referenced_table: str
    referenced_column: str


class IndexMetadata(BaseModel):
    """Metadata for a PostgreSQL table index."""

    name: str
    columns: list[str]
    is_unique: bool
    is_primary: bool
    index_type: str


class TableMetadata(BaseModel):
    """Complete catalog metadata for one introspected table."""

    schema_name: str
    table_name: str
    estimated_row_count: int
    total_size_bytes: int
    columns: list[ColumnMetadata]
    primary_key_columns: list[str]
    foreign_keys: list[ForeignKeyMetadata]
    indexes: list[IndexMetadata]


class SchemaIntrospectionResponse(BaseModel):
    """Sanitized PostgreSQL schema introspection payload for a connection."""

    connection_id: str
    dialect: Literal["postgresql"] = "postgresql"
    read_only: bool = True
    schemas: list[str]
    table_count: int
    tables: list[TableMetadata]
