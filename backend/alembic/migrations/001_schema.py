"""Initial schema (SQL)

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00

Полная схема: users, accounts, transactions, ledger_entries, audit_logs,
transfers, idempotency_keys, outbox_events. DDL в sql/001_schema.sql
"""
import os
from alembic import op

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def _read_sql(name: str) -> str:
    """Read SQL file from migrations/sql/ directory."""
    base = os.path.dirname(__file__)
    path = os.path.join(base, "sql", name)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def upgrade() -> None:
    """Apply 001_schema.sql: first enum types, then tables."""
    sql = _read_sql("001_schema.sql")
    # Run enum creation first, then tables (ensures types exist before use)
    sep = "\n-- -----------------------------------------------------------------------------\n-- users\n"
    parts = sql.split(sep, 1)
    op.execute(parts[0].strip())
    if len(parts) > 1:
        op.execute(sep.strip() + "\n" + parts[1])


def downgrade() -> None:
    """Apply 001_schema_down.sql."""
    op.execute(_read_sql("001_schema_down.sql"))
