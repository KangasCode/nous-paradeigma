"""
Pydantic schemas for checkout flow
"""
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

class CheckoutSessionCreate(BaseModel):
    plan: str = Field(..., pattern="^(starlight|cosmic|celestial|lifetime)$")

class CheckoutEmailStep(BaseModel):
    session_id: str
    email: EmailStr

class CheckoutPhoneStep(BaseModel):
    session_id: str
    phone: str = Field(..., min_length=7, max_length=20)

class CheckoutAddressStep(BaseModel):
    session_id: str
    address_line1: str = Field(..., min_length=3)
    city: str = Field(..., min_length=2)
    postal_code: str = Field(..., min_length=3)
    country: str = Field(..., min_length=2)

class CheckoutBirthdateStep(BaseModel):
    """
    Birth date step - CRITICAL DATA that cannot be changed later.
    User enters birth date twice for confirmation.
    Zodiac sign is auto-calculated from birth_date.
    """
    session_id: str
    birth_date: str = Field(..., min_length=10, max_length=10)  # YYYY-MM-DD
    birth_time: Optional[str] = None  # HH:MM (optional)
    birth_city: str = Field(..., min_length=2)
    zodiac_sign: Optional[str] = None  # Auto-calculated by frontend

class CheckoutProgressResponse(BaseModel):
    session_id: str
    current_step: str
    selected_plan: str
    email: Optional[str] = None
    phone: Optional[str] = None
    birth_date: Optional[str] = None
    zodiac_sign: Optional[str] = None
    step_email_completed: bool
    step_phone_completed: bool
    step_address_completed: bool
    step_birthdate_completed: bool = False
    
    class Config:
        from_attributes = True

class CheckoutAnalytics(BaseModel):
    total_started: int
    step_email_completed: int
    step_phone_completed: int
    step_address_completed: int
    step_payment_initiated: int
    step_payment_completed: int
    conversion_rate: float

class WaitlistSubmit(BaseModel):
    session_id: str
    email: EmailStr

class WaitlistResponse(BaseModel):
    success: bool
    message: str

