"""Add app_meta.llm_token_ledger for EvalLaps FinOps & LLMOps accounting.

Revision ID: 0003_add_llm_token_ledger
Revises: 0002_cancelled_status
Create Date: 2026-11-21 11:47:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0003_add_llm_token_ledger"
down_revision: str | Sequence[str] | None = "0002_cancelled_status"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "llm_token_ledger",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "run_id",
            UUID(as_uuid=True),
            sa.ForeignKey("app_meta.query_runs.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("stage_id", sa.String(length=32), nullable=False),
        sa.Column("provider_name", sa.String(length=32), nullable=False),
        sa.Column("model_name", sa.String(length=64), nullable=False),
        sa.Column("key_fingerprint", sa.String(length=16), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completion_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "estimated_savings_usd",
            sa.Numeric(precision=10, scale=6),
            nullable=False,
            server_default="0.000000",
        ),
        sa.Column(
            "real_cost_usd",
            sa.Numeric(precision=10, scale=6),
            nullable=False,
            server_default="0.000000",
        ),
        sa.Column("http_status", sa.Integer(), nullable=False, server_default="200"),
        sa.Column("latency_ms", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        schema="app_meta",
    )
    op.create_index(
        "ix_llm_token_ledger_recorded_at",
        "llm_token_ledger",
        ["recorded_at"],
        schema="app_meta",
    )
    op.create_index(
        "ix_llm_token_ledger_provider_recorded",
        "llm_token_ledger",
        ["provider_name", "recorded_at"],
        schema="app_meta",
    )
    op.create_index(
        "ix_llm_token_ledger_run_id",
        "llm_token_ledger",
        ["run_id"],
        schema="app_meta",
    )


def downgrade() -> None:
    op.drop_index("ix_llm_token_ledger_run_id", table_name="llm_token_ledger", schema="app_meta")
    op.drop_index(
        "ix_llm_token_ledger_provider_recorded",
        table_name="llm_token_ledger",
        schema="app_meta",
    )
    op.drop_index(
        "ix_llm_token_ledger_recorded_at",
        table_name="llm_token_ledger",
        schema="app_meta",
    )
    op.drop_table("llm_token_ledger", schema="app_meta")
