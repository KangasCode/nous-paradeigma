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
    address_line2: Optional[str] = None
    city: str = Field(..., min_length=2)
    postal_code: str = Field(..., min_length=3)
    country: str = Field(..., min_length=2)

class CheckoutProgressResponse(BaseModel):
    session_id: str
    current_step: str
    selected_plan: str
    email: Optional[str] = None
    phone: Optional[str] = None
    step_email_completed: bool
    step_phone_completed: bool
    step_address_completed: bool
    
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

