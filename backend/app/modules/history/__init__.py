"""Query-run telemetry recording in the isolated app_meta schema."""

from app.modules.history.repository import QueryRunRecordInput, QueryRunRepository

__all__ = ["QueryRunRecordInput", "QueryRunRepository"]
