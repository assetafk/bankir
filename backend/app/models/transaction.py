from enum import Enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class TransactionStatus(str, Enum):
    """Values must match PostgreSQL enum public.transactionstatus (lowercase in DB)."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    from_account_id = Column(
        Integer, ForeignKey("accounts.id"), nullable=True, index=True
    )
    to_account_id = Column(
        Integer, ForeignKey("accounts.id"), nullable=False, index=True
    )
    amount = Column(Numeric(20, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    status = Column(
        SQLEnum(TransactionStatus),
        nullable=False,
        default=TransactionStatus.PENDING,
        index=True,
    )
    is_deleted = Column(Boolean, nullable=False, default=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    failure_reason = Column(Text, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    from_account = relationship(
        "Account",
        foreign_keys=[from_account_id],
        back_populates="sent_transactions",
    )
    to_account = relationship(
        "Account",
        foreign_keys=[to_account_id],
        back_populates="received_transactions",
    )
