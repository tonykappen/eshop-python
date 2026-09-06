"""Ensure catalog.outbox exists (idempotent).

Revision ID: c4e8a1b9d2f3
Revises: 86bbeb18ee91
Create Date: 2026-02-13

Creates catalog.outbox and indexes when the table is missing (e.g. DB drift or
partial applies). Matches catalog OutboxORM / initial migration shape.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

revision = "c4e8a1b9d2f3"
down_revision = "86bbeb18ee91"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS catalog")
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = inspector.get_table_names(schema="catalog")
    if "outbox" in tables:
        return

    op.create_table(
        "outbox",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=255), nullable=False),
        sa.Column("event_data", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column("max_retries", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
        sa.Column("claimed_by", sa.String(length=255), nullable=True),
        sa.Column("claimed_at", sa.DateTime(), nullable=True),
        sa.Column("correlation_id", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="catalog",
    )
    op.create_index(
        "ix_outbox_status_created_at",
        "outbox",
        ["status", "created_at"],
        schema="catalog",
    )


def downgrade() -> None:
    """No-op: avoid desync with earlier revisions."""
    pass
