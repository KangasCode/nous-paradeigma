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
    
    # Birth data (collected at checkout, set ONCE, NEVER editable)
    birth_date = Column(String, nullable=True)  # YYYY-MM-DD
    birth_time = Column(String, nullable=True)  # HH:MM
    birth_city = Column(String, nullable=True)
    zodiac_sign = Column(String, nullable=True)  # Auto-calculated
    
    # Language for predictions (derived from country)
    prediction_language = Column(String, default="en")  # fi, en, sv, etc.
    
    # Tracking which steps completed
    step_email_completed = Column(Boolean, default=False)
    step_phone_completed = Column(Boolean, default=False)
    step_address_completed = Column(Boolean, default=False)
    step_birthdate_completed = Column(Boolean, default=False)
    step_payment_initiated = Column(Boolean, default=False)
    step_payment_completed = Column(Boolean, default=False)
    
    # Timestamps for funnel analysis
    created_at = Column(DateTime, default=datetime.utcnow)
    email_completed_at = Column(DateTime)
    phone_completed_at = Column(DateTime)
    address_completed_at = Column(DateTime)
    birthdate_completed_at = Column(DateTime)
    payment_initiated_at = Column(DateTime)
    payment_completed_at = Column(DateTime)
    
    # Which pricing tier they selected
    selected_plan = Column(String)  # starlight, cosmic, celestial, lifetime
    
    # Final outcome
    converted = Column(Boolean, default=False)


class Waitlist(Base):
    """Track waitlist submissions from capacity check step"""
    __tablename__ = "waitlist"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    email = Column(String, index=True, nullable=False)
    
    # Optional: track which plan they were trying to purchase
    selected_plan = Column(String)
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    notified = Column(Boolean, default=False)  # Track if we've notified them about opening
    notified_at = Column(DateTime, nullable=True)

