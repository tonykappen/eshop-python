"""Move catalog tables to catalog schema

Revision ID: 539d3a59b53b
Revises: 19c94aa27f18
Create Date: 2025-10-17 21:41:42.859307

"""


from alembic import op

# revision identifiers, used by Alembic.
revision = "539d3a59b53b"
down_revision = "19c94aa27f18"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Move catalog tables from public schema to catalog schema.

    This migration is only needed for databases that had tables in public schema.
    Fresh databases have tables created directly in catalog schema, so this is a no-op.
    """
    from sqlalchemy import text
    from sqlalchemy.exc import ProgrammingError

    connection = op.get_bind()

    # Helper function to check if a table exists in public schema
    def table_exists_in_public(table_name: str) -> bool:
        """Check if a table exists in the public schema."""
        try:
            result = connection.execute(
                text(
                    "SELECT EXISTS ("
                    "  SELECT FROM information_schema.tables "
                    "  WHERE table_schema = 'public' "
                    "  AND table_name = :table_name"
                    ")"
                ),
                {"table_name": table_name},
            )
            return result.scalar()
        except Exception:
            return False

    # Only move tables if they exist in public schema
    # For fresh databases, tables are created directly in catalog schema, so this is a no-op
    tables_to_move = ["catalog_brands", "catalog_categories", "catalog_items"]

    for table_name in tables_to_move:
        try:
            if table_exists_in_public(table_name):
                op.execute(text(f"ALTER TABLE {table_name} SET SCHEMA catalog"))
        except (ProgrammingError, Exception):
            # Table doesn't exist or already moved - this is expected for fresh databases
            pass


def downgrade() -> None:
    """Move catalog tables back to public schema."""
    # Move catalog_brands table back to public
    op.execute("ALTER TABLE catalog.catalog_brands SET SCHEMA public")

    # Move catalog_categories table back to public
    op.execute("ALTER TABLE catalog.catalog_categories SET SCHEMA public")

    # Move catalog_items table back to public
    op.execute("ALTER TABLE catalog.catalog_items SET SCHEMA public")
