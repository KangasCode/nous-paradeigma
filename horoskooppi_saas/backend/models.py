"""
Database models for the application
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    """User model for authentication (Magic Link only - no password)"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)  # Deprecated - kept for backwards compatibility
    
    # Profile Data
    full_name = Column(String)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    address = Column(String, nullable=True)
    
    # Birth Data (immutable after registration - used for predictions)
    birth_date = Column(String, nullable=True)  # YYYY-MM-DD - CANNOT BE CHANGED
    birth_time = Column(String, nullable=True)  # HH:MM - CANNOT BE CHANGED
    birth_city = Column(String, nullable=True)  # CANNOT BE CHANGED
    zodiac_sign = Column(String, nullable=True)  # Auto-calculated from birth_date - NEVER EDITABLE
    
    # Prediction language (derived from country at checkout)
    prediction_language = Column(String, default="en")  # fi, en, sv, etc.
    
    is_active = Column(Boolean, default=True)
    is_subscriber = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    subscriptions = relationship("Subscription", back_populates="user")
    horoscopes = relationship("Horoscope", back_populates="user")

class Subscription(Base):
    """Subscription model for Stripe billing"""
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    stripe_customer_id = Column(String, unique=True, index=True)
    stripe_subscription_id = Column(String, unique=True, index=True)
    status = Column(String, default="inactive")  # active, inactive, canceled, past_due
    current_period_start = Column(DateTime)
    current_period_end = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="subscriptions")

class Horoscope(Base):
    """Horoscope predictions generated for users"""
    __tablename__ = "horoscopes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    zodiac_sign = Column(String, nullable=False)  # aries, taurus, etc.
    prediction_type = Column(String, default="daily")  # daily, weekly, monthly
    content = Column(Text, nullable=False)
    raw_data = Column(Text, nullable=True) # JSON string of calculation data
    created_at = Column(DateTime, default=datetime.utcnow)
    prediction_date = Column(DateTime, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="horoscopes")


class MagicLinkToken(Base):
    """
    Magic link tokens for passwordless authentication.
    - Single use only
    - Expires after 10 minutes
    - Tied to a specific user
    """
    __tablename__ = "magic_link_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
