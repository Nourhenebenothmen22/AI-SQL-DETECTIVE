from typing import Literal

from pydantic import BaseModel


class ConnectionSummary(BaseModel):
    """Sanitized metadata for a preconfigured read-only database connection.

    Never exposes DSNs, hosts, ports, usernames, or passwords.
    """

    id: str
    display_name: str
    description: str
    dialect: Literal["postgresql"]
    read_only: bool
    target_schemas: list[str]
    statement_timeout_ms: int
    max_rows: int
    is_default: bool


class ConnectionListResponse(BaseModel):
    """List of available backend-configured read-only connections."""

    default_connection_id: str
    connections: list[ConnectionSummary]
