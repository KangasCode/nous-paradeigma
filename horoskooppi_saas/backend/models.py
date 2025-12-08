"""
Database models for the application
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    """User model for authentication"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    
    # Birth Data
    birth_date = Column(String, nullable=True) # YYYY-MM-DD
    birth_time = Column(String, nullable=True) # HH:MM
    birth_city = Column(String, nullable=True)
    
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
