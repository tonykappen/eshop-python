"""Ensure basket.outbox exists (idempotent).

Revision ID: b5c2a8d3e1f4
Revises: ab74ed489aa6
Create Date: 2026-02-13

Some databases were created or stamped before ``outbox`` was included in the
initial revision, or migrations were never applied. This revision creates the
table and indexes only when they are missing.
"""

import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "b5c2a8d3e1f4"
down_revision = "ab74ed489aa6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS basket")
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = inspector.get_table_names(schema="basket")
    if "outbox" in tables:
        return

    op.create_table(
        "outbox",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=255), nullable=False),
        sa.Column("event_data", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_retries", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
        sa.Column("correlation_id", sa.String(length=255), nullable=True),
        sa.Column("trace_context", postgresql.JSONB(), nullable=True),
        sa.Column("baggage", postgresql.JSONB(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="basket",
    )
    op.create_index("ix_outbox_status", "outbox", ["status"], schema="basket")
    op.create_index("ix_outbox_created_at", "outbox", ["created_at"], schema="basket")


def downgrade() -> None:
    """No-op: dropping outbox can desync from ab74ed489aa6; use full schema downgrade if needed."""
    pass
