from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.database.base import Base

APP_META_SCHEMA = "app_meta"


class QueryRun(Base):
    """Auditable telemetry record for every AI or manual SQL execution."""

    __tablename__ = "query_runs"
    __table_args__ = (
        CheckConstraint("mode IN ('nl', 'manual_sql')", name="mode_valid"),
        CheckConstraint("security_status IN ('passed', 'blocked')", name="security_status_valid"),
        CheckConstraint(
            "execution_status IN ('success', 'error', 'timeout', 'skipped', 'cancelled')",
            name="execution_status_valid",
        ),
        Index("ix_query_runs_created_at", "created_at"),
        Index("ix_query_runs_connection_id_created_at", "connection_id", "created_at"),
        {"schema": APP_META_SCHEMA},
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    connection_id: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(120), nullable=False, server_default="local-dev")
    mode: Mapped[str] = mapped_column(String(24), nullable=False)
    natural_language_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_sql: Mapped[str | None] = mapped_column(Text, nullable=True)
    validated_sql: Mapped[str | None] = mapped_column(Text, nullable=True)
    security_status: Mapped[str] = mapped_column(String(24), nullable=False)
    security_violations_json: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    review_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    execution_status: Mapped[str] = mapped_column(String(24), nullable=False)
    execution_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    was_truncated: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    explain_plan_json: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(
        JSONB, nullable=True
    )
    explanation_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    optimizations_json: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB, nullable=True)
    langsmith_run_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
