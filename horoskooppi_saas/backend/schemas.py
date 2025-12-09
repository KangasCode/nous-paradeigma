"""
Pydantic models for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    """
    Schema for user registration (Magic Link - no password required).
    Birth data is set ONCE during registration and CANNOT be changed later.
    The zodiac sign is automatically calculated from birth_date.
    """
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    # Birth data - IMMUTABLE after registration
    birth_date: Optional[str] = None  # YYYY-MM-DD - Cannot be changed
    birth_time: Optional[str] = None  # HH:MM - Cannot be changed
    birth_city: Optional[str] = None  # Cannot be changed
    prediction_language: Optional[str] = "en"  # Derived from country

class MagicLinkRequest(BaseModel):
    """Request a magic link to be sent to email."""
    email: EmailStr

class MagicLinkResponse(BaseModel):
    """Response after requesting magic link - always the same for security."""
    message: str = "If the email exists, a login link has been sent."
    success: bool = True

class UserProfileUpdate(BaseModel):
    """
    Schema for updating user profile.
    NOTE: birth_date, birth_city, and zodiac_sign are NOT included
    because they CANNOT be changed after registration.
    Birth time CAN be added/updated by the user.
    """
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    full_name: Optional[str] = None
    # Birth time can be added/updated (for more precise predictions)
    birth_time: Optional[str] = None

class UserResponse(UserBase):
    id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    birth_date: Optional[str] = None
    birth_time: Optional[str] = None
    birth_city: Optional[str] = None
    zodiac_sign: Optional[str] = None  # Auto-calculated, never editable
    is_active: bool
    is_subscriber: bool
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# Subscription Schemas
class SubscriptionBase(BaseModel):
    status: str
    current_period_end: Optional[datetime] = None

class SubscriptionResponse(SubscriptionBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Horoscope Schemas
class HoroscopeCreate(BaseModel):
    zodiac_sign: str = Field(..., min_length=3, max_length=20)
    prediction_type: str = Field(default="daily", pattern="^(daily|weekly|monthly)$")

class HoroscopeResponse(BaseModel):
    id: int
    zodiac_sign: str
    prediction_type: str
    content: str
    raw_data: Optional[str] = None
    created_at: datetime
    prediction_date: datetime

    class Config:
        from_attributes = True

class CheckoutSessionCreate(BaseModel):
    price_id: str
