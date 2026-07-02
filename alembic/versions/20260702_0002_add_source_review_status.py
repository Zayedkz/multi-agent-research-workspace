"""add source review status

Revision ID: 20260702_0002
Revises: 20260701_0001
Create Date: 2026-07-02 15:25:00
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260702_0002"
down_revision: str | None = "20260701_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "research_sources",
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
            server_default="candidate",
        ),
    )
    op.add_column(
        "research_sources",
        sa.Column("review_note", sa.Text(), nullable=True),
    )
    op.add_column(
        "research_sources",
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.alter_column("research_sources", "status", server_default=None)


def downgrade() -> None:
    op.drop_column("research_sources", "reviewed_at")
    op.drop_column("research_sources", "review_note")
    op.drop_column("research_sources", "status")
