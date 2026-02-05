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
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class TransferStatus(str, Enum):
    """Values must match PostgreSQL enum public.transferstatus (lowercase in DB)."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class Transfer(Base):
    __tablename__ = "transfers"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(
        Integer,
        ForeignKey("transactions.id"),
        nullable=False,
        unique=True,
        index=True,
    )
    from_account_id = Column(
        Integer, ForeignKey("accounts.id"), nullable=False, index=True
    )
    to_account_id = Column(
        Integer, ForeignKey("accounts.id"), nullable=False, index=True
    )
    amount = Column(Numeric(20, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    status = Column(
        SQLEnum(TransferStatus),
        nullable=False,
        default=TransferStatus.PENDING,
        index=True,
    )
    idempotency_key = Column(String(255), nullable=True, index=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    transaction = relationship("Transaction", backref="transfer")
    from_account = relationship("Account", foreign_keys=[from_account_id])
    to_account = relationship("Account", foreign_keys=[to_account_id])

    __table_args__ = (
        Index(
            "ix_transfers_idempotency_from_to",
            "idempotency_key",
            "from_account_id",
            "to_account_id",
        ),
    )
