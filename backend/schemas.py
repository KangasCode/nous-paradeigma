"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    is_subscriber: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    email: Optional[str] = None

# Subscription schemas
class SubscriptionResponse(BaseModel):
    id: int
    user_id: int
    status: str
    current_period_start: Optional[datetime]
    current_period_end: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Horoscope schemas
class HoroscopeCreate(BaseModel):
    zodiac_sign: str = Field(..., pattern="^(aries|taurus|gemini|cancer|leo|virgo|libra|scorpio|sagittarius|capricorn|aquarius|pisces)$")
    prediction_type: str = Field(default="daily", pattern="^(daily|weekly|monthly)$")

class HoroscopeResponse(BaseModel):
    id: int
    zodiac_sign: str
    prediction_type: str
    content: str
    created_at: datetime
    prediction_date: datetime
    
    class Config:
        from_attributes = True

# Stripe schemas
class CheckoutSessionCreate(BaseModel):
    price_id: str

class StripeWebhookEvent(BaseModel):
    type: str
    data: dict

