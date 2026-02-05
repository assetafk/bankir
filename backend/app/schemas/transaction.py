from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.core.xss_protection import sanitize_string_field, validate_no_xss_patterns
from app.models.transaction import TransactionStatus


class TransactionBase(BaseModel):
    amount: Decimal = Field(..., gt=0, description="Transfer amount")
    currency: str = Field(
        ..., min_length=3, max_length=3, description="ISO 4217 currency code"
    )

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Sanitize currency code to prevent XSS"""
        sanitized = sanitize_string_field(v, max_length=3).upper()
        if not validate_no_xss_patterns(sanitized):
            raise ValueError("Currency code contains invalid characters")
        return sanitized


class TransferCreate(TransactionBase):
    from_account_id: int = Field(..., description="Source account ID")
    to_account_id: int = Field(..., description="Destination account ID")
    idempotency_key: Optional[str] = Field(
        None, description="Idempotency key for duplicate prevention"
    )

    @field_validator("idempotency_key")
    @classmethod
    def validate_idempotency_key(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize idempotency key to prevent XSS"""
        if v is None:
            return None
        sanitized = sanitize_string_field(v, max_length=255)
        if not validate_no_xss_patterns(sanitized):
            raise ValueError("Idempotency key contains invalid characters")
        return sanitized


class TransactionResponse(TransactionBase):
    id: int
    from_account_id: Optional[int]
    to_account_id: int
    status: TransactionStatus
    created_at: datetime

    class Config:
        from_attributes = True


class TransactionHistoryQuery(BaseModel):
    account_id: Optional[int] = None
    status: Optional[TransactionStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
