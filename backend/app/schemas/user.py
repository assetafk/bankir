from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime
from typing import Optional
from app.core.xss_protection import sanitize_email, sanitize_string_field, validate_no_xss_patterns


class UserBase(BaseModel):
    email: EmailStr

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Sanitize and validate email to prevent XSS"""
        return sanitize_email(v)


class UserCreate(UserBase):
    password: str

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password doesn't contain XSS patterns"""
        if not validate_no_xss_patterns(v):
            raise ValueError("Password contains invalid characters")
        return v


class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None
