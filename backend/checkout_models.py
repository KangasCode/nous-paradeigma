"""
Checkout funnel tracking models
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class CheckoutProgress(Base):
    """Track user progress through checkout funnel"""
    __tablename__ = "checkout_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True, nullable=False)
    
    # User data collected during checkout
    email = Column(String, index=True)
    phone = Column(String)
    address_line1 = Column(String)
    address_line2 = Column(String)
    city = Column(String)
    postal_code = Column(String)
    country = Column(String)
    
    # Tracking which steps completed
    step_email_completed = Column(Boolean, default=False)
    step_phone_completed = Column(Boolean, default=False)
    step_address_completed = Column(Boolean, default=False)
    step_payment_initiated = Column(Boolean, default=False)
    step_payment_completed = Column(Boolean, default=False)
    
    # Timestamps for funnel analysis
    created_at = Column(DateTime, default=datetime.utcnow)
    email_completed_at = Column(DateTime)
    phone_completed_at = Column(DateTime)
    address_completed_at = Column(DateTime)
    payment_initiated_at = Column(DateTime)
    payment_completed_at = Column(DateTime)
    
    # Which pricing tier they selected
    selected_plan = Column(String)  # starlight, cosmic, celestial, lifetime
    
    # Final outcome
    converted = Column(Boolean, default=False)

