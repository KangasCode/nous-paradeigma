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
    birth_date: Optional[str] = None
    birth_time: Optional[str] = None
    birth_city: Optional[str] = None

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
