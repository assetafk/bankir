from pydantic import BaseModel, Field, field_validator
from decimal import Decimal
from datetime import datetime
from typing import Optional
from app.core.xss_protection import sanitize_string_field, validate_no_xss_patterns


class AccountBase(BaseModel):
    currency: str = Field(..., min_length=3, max_length=3, description="ISO 4217 currency code")

    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Sanitize currency code to prevent XSS"""
        sanitized = sanitize_string_field(v, max_length=3).upper()
        if not validate_no_xss_patterns(sanitized):
            raise ValueError("Currency code contains invalid characters")
        return sanitized


class AccountCreate(AccountBase):
    initial_balance: Optional[Decimal] = Field(default=Decimal("0.00"), ge=0)


class AccountResponse(AccountBase):
    id: int
    user_id: int
    balance: Decimal
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
