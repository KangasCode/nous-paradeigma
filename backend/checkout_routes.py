"""
Checkout funnel routes and tracking
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
import secrets

from database import get_db
from checkout_models import CheckoutProgress
from checkout_schemas import (
    CheckoutSessionCreate, CheckoutEmailStep, CheckoutPhoneStep,
    CheckoutAddressStep, CheckoutProgressResponse, CheckoutAnalytics
)
from stripe_webhooks import create_checkout_session
import os

router = APIRouter(prefix="/api/checkout", tags=["checkout"])

# Plan to Stripe Price ID mapping
PLAN_PRICE_MAP = {
    "starlight": os.getenv("STRIPE_PRICE_ID_STARLIGHT", os.getenv("STRIPE_PRICE_ID")),
    "cosmic": os.getenv("STRIPE_PRICE_ID_COSMIC", os.getenv("STRIPE_PRICE_ID")),
    "celestial": os.getenv("STRIPE_PRICE_ID_CELESTIAL", os.getenv("STRIPE_PRICE_ID")),
    "lifetime": os.getenv("STRIPE_PRICE_ID_LIFETIME", os.getenv("STRIPE_PRICE_ID")),
}

@router.post("/start", response_model=CheckoutProgressResponse)
async def start_checkout(data: CheckoutSessionCreate, db: Session = Depends(get_db)):
    """
    Start a new checkout session
    """
    # Generate unique session ID
    session_id = secrets.token_urlsafe(32)
    
    # Create checkout progress record
    progress = CheckoutProgress(
        session_id=session_id,
        selected_plan=data.plan
    )
    
    db.add(progress)
    db.commit()
    db.refresh(progress)
    
    return CheckoutProgressResponse(
        session_id=session_id,
        current_step="email",
        selected_plan=data.plan,
        step_email_completed=False,
        step_phone_completed=False,
        step_address_completed=False
    )

@router.post("/step/email", response_model=CheckoutProgressResponse)
async def save_email_step(data: CheckoutEmailStep, db: Session = Depends(get_db)):
    """
    Save email and mark email step as completed
    """
    progress = db.query(CheckoutProgress).filter(
        CheckoutProgress.session_id == data.session_id
    ).first()
    
    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Checkout session not found"
        )
    
    progress.email = data.email
    progress.step_email_completed = True
    progress.email_completed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(progress)
    
    return CheckoutProgressResponse(
        session_id=progress.session_id,
        current_step="phone",
        selected_plan=progress.selected_plan,
        email=progress.email,
        step_email_completed=True,
        step_phone_completed=False,
        step_address_completed=False
    )

@router.post("/step/phone", response_model=CheckoutProgressResponse)
async def save_phone_step(data: CheckoutPhoneStep, db: Session = Depends(get_db)):
    """
    Save phone and mark phone step as completed
    """
    progress = db.query(CheckoutProgress).filter(
        CheckoutProgress.session_id == data.session_id
    ).first()
    
    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Checkout session not found"
        )
    
    progress.phone = data.phone
    progress.step_phone_completed = True
    progress.phone_completed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(progress)
    
    return CheckoutProgressResponse(
        session_id=progress.session_id,
        current_step="address",
        selected_plan=progress.selected_plan,
        email=progress.email,
        phone=progress.phone,
        step_email_completed=True,
        step_phone_completed=True,
        step_address_completed=False
    )

@router.post("/step/address", response_model=CheckoutProgressResponse)
async def save_address_step(data: CheckoutAddressStep, db: Session = Depends(get_db)):
    """
    Save address and mark address step as completed
    """
    progress = db.query(CheckoutProgress).filter(
        CheckoutProgress.session_id == data.session_id
    ).first()
    
    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Checkout session not found"
        )
    
    progress.address_line1 = data.address_line1
    progress.address_line2 = data.address_line2
    progress.city = data.city
    progress.postal_code = data.postal_code
    progress.country = data.country
    progress.step_address_completed = True
    progress.address_completed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(progress)
    
    return CheckoutProgressResponse(
        session_id=progress.session_id,
        current_step="payment",
        selected_plan=progress.selected_plan,
        email=progress.email,
        phone=progress.phone,
        step_email_completed=True,
        step_phone_completed=True,
        step_address_completed=True
    )

@router.post("/create-payment")
async def create_payment_session(session_id: str, db: Session = Depends(get_db)):
    """
    Create Stripe checkout session after all steps completed
    OR complete in demo mode if Stripe not configured
    """
    progress = db.query(CheckoutProgress).filter(
        CheckoutProgress.session_id == session_id
    ).first()
    
    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Checkout session not found"
        )
    
    if not progress.step_address_completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Complete all checkout steps first"
        )
    
    # Mark payment initiated
    progress.step_payment_initiated = True
    progress.payment_initiated_at = datetime.utcnow()
    
    # Check if we're in DEMO MODE (no Stripe configured)
    stripe_key = os.getenv("STRIPE_SECRET_KEY")
    demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
    
    if demo_mode or not stripe_key or stripe_key.startswith("sk_test_your") or stripe_key == "your-stripe-secret-key":
        # DEMO MODE: Complete checkout without payment
        print(f"✅ DEMO MODE: Checkout completed for {progress.email} - Plan: {progress.selected_plan}")
        
        progress.step_payment_completed = True
        progress.payment_completed_at = datetime.utcnow()
        progress.converted = True
        db.commit()
        
        base_url = os.getenv("BASE_URL", "http://localhost:8000")
        return {
            "checkout_url": f"{base_url}/success?demo=true",
            "session_id": session_id,
            "demo_mode": True
        }
    
    # PRODUCTION MODE: Use real Stripe
    price_id = PLAN_PRICE_MAP.get(progress.selected_plan)
    if not price_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Price ID not configured for this plan"
        )
    
    db.commit()
    
    # Create Stripe checkout session
    base_url = os.getenv("BASE_URL", "http://localhost:8000")
    
    stripe_session = create_checkout_session(
        price_id=price_id,
        customer_email=progress.email,
        success_url=f"{base_url}/success",
        cancel_url=f"{base_url}/cancel"
    )
    
    return {"checkout_url": stripe_session.url, "session_id": session_id, "demo_mode": False}

@router.get("/progress/{session_id}", response_model=CheckoutProgressResponse)
async def get_checkout_progress(session_id: str, db: Session = Depends(get_db)):
    """
    Get current checkout progress for a session
    """
    progress = db.query(CheckoutProgress).filter(
        CheckoutProgress.session_id == session_id
    ).first()
    
    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Checkout session not found"
        )
    
    # Determine current step
    current_step = "email"
    if progress.step_address_completed:
        current_step = "payment"
    elif progress.step_phone_completed:
        current_step = "address"
    elif progress.step_email_completed:
        current_step = "phone"
    
    return CheckoutProgressResponse(
        session_id=progress.session_id,
        current_step=current_step,
        selected_plan=progress.selected_plan,
        email=progress.email,
        phone=progress.phone,
        step_email_completed=progress.step_email_completed,
        step_phone_completed=progress.step_phone_completed,
        step_address_completed=progress.step_address_completed
    )

@router.get("/analytics", response_model=CheckoutAnalytics)
async def get_checkout_analytics(db: Session = Depends(get_db)):
    """
    Get checkout funnel analytics (admin only in production)
    """
    total_started = db.query(CheckoutProgress).count()
    email_completed = db.query(CheckoutProgress).filter(
        CheckoutProgress.step_email_completed == True
    ).count()
    phone_completed = db.query(CheckoutProgress).filter(
        CheckoutProgress.step_phone_completed == True
    ).count()
    address_completed = db.query(CheckoutProgress).filter(
        CheckoutProgress.step_address_completed == True
    ).count()
    payment_initiated = db.query(CheckoutProgress).filter(
        CheckoutProgress.step_payment_initiated == True
    ).count()
    payment_completed = db.query(CheckoutProgress).filter(
        CheckoutProgress.step_payment_completed == True
    ).count()
    
    conversion_rate = (payment_completed / total_started * 100) if total_started > 0 else 0
    
    return CheckoutAnalytics(
        total_started=total_started,
        step_email_completed=email_completed,
        step_phone_completed=phone_completed,
        step_address_completed=address_completed,
        step_payment_initiated=payment_initiated,
        step_payment_completed=payment_completed,
        conversion_rate=round(conversion_rate, 2)
    )

# Submissions endpoint removed - use /analytics dashboard instead for privacy

