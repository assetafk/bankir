from enum import Enum

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.sql import func

from app.database import Base


class LedgerEntryType(str, Enum):
    DEBIT = "debit"
    CREDIT = "credit"


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(
        Integer, ForeignKey("transactions.id"), nullable=False, index=True
    )
    account_id = Column(
        Integer, ForeignKey("accounts.id"), nullable=False, index=True
    )
    entry_type = Column(SQLEnum(LedgerEntryType), nullable=False, index=True)
    amount = Column(Numeric(20, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    balance_before = Column(Numeric(20, 2), nullable=False)
    balance_after = Column(Numeric(20, 2), nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    __table_args__ = (
        Index("idx_ledger_account_created", "account_id", "created_at"),
    )
