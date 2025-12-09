"""
FastAPI main application
"""
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import os
import json

from database import get_db, init_db, init_test_data_if_needed
from models import User, Horoscope, Subscription
from schemas import (
    UserCreate, UserLogin, UserResponse, Token,
    HoroscopeCreate, HoroscopeResponse, SubscriptionResponse
)
from auth import (
    get_password_hash, authenticate_user, create_access_token,
    get_current_active_user, get_current_subscriber, get_user_by_email
)
from gemini_client import gemini_client
from stripe_webhooks import (
    StripeWebhookHandler, create_checkout_session, create_customer_portal_session
)
from checkout_routes import router as checkout_router

# Create FastAPI app
app = FastAPI(
    title="Horoskooppi SaaS",
    description="AI-powered horoscope subscription service",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(checkout_router)

# Explicitly resolve paths relative to this file
# backend/main.py -> backend/ -> horoskooppi_saas/ -> frontend/static
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # backend/
PROJECT_ROOT = os.path.dirname(BASE_DIR) # horoskooppi_saas/
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")
STATIC_DIR = os.path.join(FRONTEND_DIR, "static")
TEMPLATES_DIR = os.path.join(FRONTEND_DIR, "templates")

# Verify paths
print(f"🔍 Path Resolution:")
print(f"   Base: {BASE_DIR}")
print(f"   Static: {STATIC_DIR}")
print(f"   Templates: {TEMPLATES_DIR}")

if not os.path.exists(STATIC_DIR):
    print(f"⚠️ WARNING: Static directory not found at {STATIC_DIR}")
else:
    print(f"✅ Static directory found")

if not os.path.exists(TEMPLATES_DIR):
    print(f"⚠️ WARNING: Templates directory not found at {TEMPLATES_DIR}")
else:
    print(f"✅ Templates directory found")

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Setup templates
from jinja2 import Environment, FileSystemLoader
jinja_env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), auto_reload=True)
templates = Jinja2Templates(env=jinja_env)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()
    print("Database initialized successfully")
    # Create test user if CREATE_TEST_USER env var is set
    init_test_data_if_needed()

# Root endpoint - serve index page (HEAD requests handled automatically by FastAPI)
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve the main landing page"""
    response = templates.TemplateResponse("index.html", {"request": request})
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# Health check endpoint for Render
@app.get("/health")
@app.head("/health")
async def health():
    """Health check endpoint for Render"""
    return {"status": "ok"}

# Setup endpoint to create test user (for production setup)
@app.get("/api/setup/test-user")
async def setup_test_user(db: Session = Depends(get_db)):
    """Create test user if it doesn't exist - for production setup"""
    from database import init_test_data_if_needed
    import os
    
    # Force enable test user creation
    os.environ["CREATE_TEST_USER"] = "true"
    
    # Check if user exists first
    existing = db.query(User).filter(User.email == "test@nousparadeigma.com").first()
    if existing:
        return {"status": "exists", "message": "Test user already exists", "email": existing.email}
    
    # Create the test user
    try:
        init_test_data_if_needed()
        return {"status": "created", "message": "Test user created successfully", "email": "test@nousparadeigma.com", "password": "cosmos123"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Debug endpoint to check file paths (remove in production)
@app.get("/api/debug/paths")
async def debug_paths():
    """Debug endpoint to check file paths"""
    return {
        "base_dir": BASE_DIR,
        "static_dir": STATIC_DIR,
        "templates_dir": TEMPLATES_DIR,
        "static_exists": os.path.exists(STATIC_DIR),
        "templates_exists": os.path.exists(TEMPLATES_DIR),
        "static_files": os.listdir(STATIC_DIR) if os.path.exists(STATIC_DIR) else [],
        "template_files": os.listdir(TEMPLATES_DIR) if os.path.exists(TEMPLATES_DIR) else [],
        "cwd": os.getcwd()
    }

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """Serve the dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/success", response_class=HTMLResponse)
async def success_page(request: Request):
    """Serve the success page"""
    return templates.TemplateResponse("success.html", {"request": request})

@app.get("/cancel", response_class=HTMLResponse)
async def cancel_page(request: Request):
    """Serve the cancel page"""
    return templates.TemplateResponse("cancel.html", {"request": request})

@app.get("/checkout", response_class=HTMLResponse)
async def checkout_page(request: Request, plan: str = "cosmic"):
    """Serve the checkout page"""
    response = templates.TemplateResponse("checkout.html", {"request": request, "plan": plan})
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.get("/analytics", response_class=HTMLResponse)
async def analytics_page(request: Request):
    """Serve the analytics dashboard"""
    return templates.TemplateResponse("analytics.html", {"request": request})

@app.get("/waitlist", response_class=HTMLResponse)
async def waitlist_page(request: Request):
    """Serve the waitlist dashboard"""
    return templates.TemplateResponse("waitlist.html", {"request": request})

# ============================================================================
# Authentication Endpoints
# ============================================================================

@app.post("/api/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    existing_user = get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        birth_date=user_data.birth_date,
        birth_time=user_data.birth_time,
        birth_city=user_data.birth_city
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@app.post("/api/auth/login", response_model=Token)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """Login and get access token"""
    try:
        print(f"Login attempt for email: {user_data.email}")
        user = authenticate_user(db, user_data.email, user_data.password)
        if not user:
            print(f"Authentication failed for: {user_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        print(f"Authentication successful for: {user_data.email}")
        # Create access token
        access_token = create_access_token(data={"sub": user.email})
        
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information"""
    return current_user

# ============================================================================
# Stripe Endpoints
# ============================================================================

@app.post("/api/stripe/create-checkout-session")
async def create_checkout(
    current_user: User = Depends(get_current_active_user)
):
    """Create a Stripe checkout session"""
    price_id = os.getenv("STRIPE_PRICE_ID")
    if not price_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stripe price ID not configured"
        )
    
    # Get base URL from environment or use default
    base_url = os.getenv("BASE_URL", "http://localhost:8000")
    
    session = create_checkout_session(
        price_id=price_id,
        customer_email=current_user.email,
        success_url=f"{base_url}/success",
        cancel_url=f"{base_url}/cancel"
    )
    
    return {"checkout_url": session.url}

@app.post("/api/stripe/create-portal-session")
async def create_portal(
    current_user: User = Depends(get_current_subscriber),
    db: Session = Depends(get_db)
):
    """Create a Stripe customer portal session"""
    # Get user's subscription
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    ).first()
    
    if not subscription or not subscription.stripe_customer_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )
    
    base_url = os.getenv("BASE_URL", "http://localhost:8000")
    
    portal_session = create_customer_portal_session(
        customer_id=subscription.stripe_customer_id,
        return_url=f"{base_url}/dashboard"
    )
    
    return {"portal_url": portal_session.url}

@app.post("/api/stripe/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe webhooks"""
    payload = await request.body()
    signature = request.headers.get("stripe-signature")
    
    if not signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing stripe-signature header"
        )
    
    # Verify and process webhook
    event = StripeWebhookHandler.verify_webhook_signature(payload, signature)
    StripeWebhookHandler.process_webhook_event(event, db)
    
    return {"status": "success"}

# ============================================================================
# Horoscope Endpoints
# ============================================================================

@app.post("/api/horoscopes/generate", response_model=HoroscopeResponse)
async def generate_horoscope(
    horoscope_data: HoroscopeCreate,
    current_user: User = Depends(get_current_subscriber),
    db: Session = Depends(get_db)
):
    """Generate a new horoscope prediction (subscribers only)"""
    # Generate horoscope using Gemini
    content, raw_data = gemini_client.generate_horoscope(
        zodiac_sign=horoscope_data.zodiac_sign,
        prediction_type=horoscope_data.prediction_type
    )
    
    # Save to database
    new_horoscope = Horoscope(
        user_id=current_user.id,
        zodiac_sign=horoscope_data.zodiac_sign,
        prediction_type=horoscope_data.prediction_type,
        content=content,
        raw_data=json.dumps(raw_data),
        prediction_date=datetime.utcnow()
    )
    
    db.add(new_horoscope)
    db.commit()
    db.refresh(new_horoscope)
    
    return new_horoscope

@app.get("/api/horoscopes/my", response_model=list[HoroscopeResponse])
async def get_my_horoscopes(
    current_user: User = Depends(get_current_subscriber),
    db: Session = Depends(get_db),
    limit: int = 10
):
    """Get current user's horoscopes (subscribers only)"""
    horoscopes = db.query(Horoscope).filter(
        Horoscope.user_id == current_user.id
    ).order_by(Horoscope.created_at.desc()).limit(limit).all()
    
    return horoscopes

@app.get("/api/horoscopes/{horoscope_id}", response_model=HoroscopeResponse)
async def get_horoscope(
    horoscope_id: int,
    current_user: User = Depends(get_current_subscriber),
    db: Session = Depends(get_db)
):
    """Get a specific horoscope (subscribers only)"""
    horoscope = db.query(Horoscope).filter(
        Horoscope.id == horoscope_id,
        Horoscope.user_id == current_user.id
    ).first()
    
    if not horoscope:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Horoscope not found"
        )
    
    return horoscope

# ============================================================================
# Subscription Endpoints
# ============================================================================

@app.get("/api/subscription/status", response_model=SubscriptionResponse)
async def get_subscription_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user's subscription status"""
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    ).first()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No subscription found"
        )
    
    return subscription

# ============================================================================
# Health Check
# ============================================================================

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
