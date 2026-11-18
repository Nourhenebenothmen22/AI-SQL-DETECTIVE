"""Add 'cancelled' to app_meta.query_runs execution_status check constraint.

Revision ID: 0002_cancelled_status
Revises: 0001_initial
Create Date: 2026-11-18 07:45:00
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0002_cancelled_status"
down_revision: str | Sequence[str] | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint(
        "ck_query_runs_execution_status_valid",
        "query_runs",
        schema="app_meta",
        type_="check",
    )
    op.create_check_constraint(
        "ck_query_runs_execution_status_valid",
        "query_runs",
        "execution_status IN ('success', 'error', 'timeout', 'skipped', 'cancelled')",
        schema="app_meta",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_query_runs_execution_status_valid",
        "query_runs",
        schema="app_meta",
        type_="check",
    )
    op.create_check_constraint(
        "ck_query_runs_execution_status_valid",
        "query_runs",
        "execution_status IN ('success', 'error', 'timeout', 'skipped')",
        schema="app_meta",
    )
