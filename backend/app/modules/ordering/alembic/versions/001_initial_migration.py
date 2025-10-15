"""Initial placeholder migration for ordering module

Revision ID: 001
Revises:
Create Date: 2025-10-10 12:00:00.000000

NOTE: This is a placeholder migration. Ordering tables will be created
when the ordering module is implemented.
"""

# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Placeholder upgrade - ordering schema created but no tables yet."""
    # Schema is created by env.py
    # Tables will be added when ordering module is implemented
    pass


def downgrade() -> None:
    """Placeholder downgrade."""
    pass
