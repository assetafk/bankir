"""Add first_name and last_name to accounts

Revision ID: 002
Revises: 001
Create Date: 2025-02-05

"""
import os
from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def _read_sql(name: str) -> str:
    base = os.path.dirname(__file__)
    path = os.path.join(base, "sql", name)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def upgrade() -> None:
    op.execute(_read_sql("002_account_names.sql"))


def downgrade() -> None:
    op.execute(_read_sql("002_account_names_down.sql"))
