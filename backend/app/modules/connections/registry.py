import json
from dataclasses import dataclass

from pydantic import BaseModel, Field, SecretStr, TypeAdapter

from app.core.config import Settings
from app.schemas.connections import ConnectionSummary

DEFAULT_CONNECTION_ID = "ecommerce_demo"


class ExtraConnectionEntry(BaseModel):
    """Schema for optional extra backend-configured read-only connections."""

    id: str = Field(min_length=1, max_length=64, pattern=r"^[a-z0-9_-]+$")
    display_name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=300)
    dsn: SecretStr
    target_schemas: list[str] = Field(min_length=1)
    statement_timeout_ms: int = Field(default=5000, ge=500, le=30000)
    max_rows: int = Field(default=200, ge=1, le=5000)


@dataclass(frozen=True, slots=True)
class DatabaseConnectionSpec:
    """Internal connection specification holding backend-only credentials."""

    id: str
    display_name: str
    description: str
    dsn: SecretStr
    target_schemas: tuple[str, ...]
    statement_timeout_ms: int
    max_rows: int
    read_only: bool = True

    def to_public_summary(self, *, is_default: bool = False) -> ConnectionSummary:
        """Return sanitized metadata safe for frontend responses."""
        return ConnectionSummary(
            id=self.id,
            display_name=self.display_name,
            description=self.description,
            dialect="postgresql",
            read_only=self.read_only,
            target_schemas=list(self.target_schemas),
            statement_timeout_ms=self.statement_timeout_ms,
            max_rows=self.max_rows,
            is_default=is_default,
        )


class ConnectionRegistry:
    """Registry of preconfigured read-only PostgreSQL connections."""

    def __init__(self, settings: Settings) -> None:
        self._connections: dict[str, DatabaseConnectionSpec] = {}
        self._default_id = DEFAULT_CONNECTION_ID

        self._connections[DEFAULT_CONNECTION_ID] = DatabaseConnectionSpec(
            id=DEFAULT_CONNECTION_ID,
            display_name="Synthetic E-Commerce Demo",
            description="Preconfigured read-only PostgreSQL 16 ecommerce dataset.",
            dsn=settings.database_ro_url,
            target_schemas=("ecommerce",),
            statement_timeout_ms=settings.sql_statement_timeout_ms,
            max_rows=settings.effective_default_max_rows,
            read_only=True,
        )

        self._load_extra_connections(settings)

    def _load_extra_connections(self, settings: Settings) -> None:
        raw_json = settings.extra_connections_json.strip()
        if not raw_json or raw_json == "[]":
            return

        adapter = TypeAdapter(list[ExtraConnectionEntry])
        entries = adapter.validate_python(json.loads(raw_json))
        for entry in entries:
            if entry.id in self._connections:
                raise ValueError(f"Duplicate database connection id configured: {entry.id!r}")
            self._connections[entry.id] = DatabaseConnectionSpec(
                id=entry.id,
                display_name=entry.display_name,
                description=entry.description,
                dsn=entry.dsn,
                target_schemas=tuple(entry.target_schemas),
                statement_timeout_ms=entry.statement_timeout_ms,
                max_rows=min(entry.max_rows, settings.sql_hard_max_rows),
                read_only=True,
            )

    @property
    def default_id(self) -> str:
        return self._default_id

    def get(self, connection_id: str | None = None) -> DatabaseConnectionSpec:
        target_id = connection_id or self._default_id
        if target_id not in self._connections:
            raise KeyError(f"Unknown preconfigured connection: {target_id!r}")
        return self._connections[target_id]

    def list_public(self) -> list[ConnectionSummary]:
        return [
            spec.to_public_summary(is_default=(spec.id == self._default_id))
            for spec in self._connections.values()
        ]
