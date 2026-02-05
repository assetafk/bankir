from enum import Enum

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SQLEnum,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.sql import func

from app.database import Base


class AuditAction(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    TRANSFER = "transfer"
    LOGIN = "login"
    LOGOUT = "logout"
    FRAUD_CHECK = "fraud_check"
    ACCOUNT_ACCESS = "account_access"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    action = Column(SQLEnum(AuditAction), nullable=False, index=True)
    resource_type = Column(
        String(50), nullable=False, index=True
    )  # account, transaction, user, etc.
    resource_id = Column(Integer, nullable=True, index=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    request_id = Column(String(100), nullable=True, index=True)
    details = Column(JSON, nullable=True)  # Additional context
    status = Column(
        String(20), nullable=False, default="success", index=True
    )  # success, failed, blocked
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
