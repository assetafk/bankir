from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    idempotency_key = Column(String(255), nullable=False, index=True)
    request_hash = Column(String(64), nullable=True)
    response_body = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)

    user = relationship("User", backref="idempotency_keys")

    __table_args__ = (
        Index(
            "uq_idempotency_user_key",
            "user_id",
            "idempotency_key",
            unique=True,
        ),
    )
