"""
FastAPI main application
"""
from fastapi import FastAPI, Depends, HTTPException, status, Request, Form, Body
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import os
import json
import secrets
from collections import defaultdict
from typing import Optional as OptionalType
from starlette.middleware.base import BaseHTTPMiddleware

from database import get_db, init_db, init_test_data_if_needed
from models import User, Horoscope, Subscription, MagicLinkToken
from schemas import (
    UserCreate, UserResponse, UserProfileUpdate, Token,
    HoroscopeCreate, HoroscopeResponse, SubscriptionResponse,
    MagicLinkRequest, MagicLinkResponse
)
from zodiac_utils import calculate_zodiac_sign
from auth import (
    create_access_token,
    get_current_active_user, get_current_subscriber, get_user_by_email
)
from gemini_client import gemini_client, GeminiAPIError
from email_service import email_service
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

# ============================================================================
# TEMPORARY SITE PASSWORD PROTECTION
# Set SITE_ACCESS_PASSWORD env var to enable password protection
# Remove this section when site goes public
# ============================================================================

SITE_ACCESS_PASSWORD = os.getenv("SITE_ACCESS_PASSWORD", "")

class SiteAccessMiddleware(BaseHTTPMiddleware):
    """
    Middleware to protect entire site with a simple password.
    Only active when SITE_ACCESS_PASSWORD environment variable is set.
    Does NOT interfere with existing JWT authentication for users.
    """
    
    # Paths that should always be accessible (without site password)
    EXCLUDED_PATHS = [
        "/access",           # The password form itself
        "/static",           # Static files (CSS, JS, images)
        "/health",           # Health check for deployment
        "/favicon.ico",      # Favicon
    ]
    
    async def dispatch(self, request: Request, call_next):
        # If no site password is set, skip this middleware entirely
        if not SITE_ACCESS_PASSWORD:
            return await call_next(request)
        
        path = request.url.path
        
        # Allow excluded paths without password
        for excluded in self.EXCLUDED_PATHS:
            if path.startswith(excluded):
                return await call_next(request)
        
        # Check for site access cookie
        site_access_granted = request.cookies.get("site_access_granted")
        
        if site_access_granted == "true":
            # Cookie is valid, allow the request
            return await call_next(request)
        
        # No valid cookie, redirect to access page
        return RedirectResponse(url="/access", status_code=302)

# ============================================================================
# IP RATE LIMITING FOR PREVIEW HOROSCOPE
# ============================================================================

# Simple in-memory cache for IP rate limiting (use Redis in production)
preview_cache = {}
BOT_USER_AGENTS = ['bot', 'crawler', 'spider', 'scraper', 'curl', 'wget', 'python-requests']

def get_client_ip(request: Request) -> str:
    """Extract client IP address from request"""
    # Check for forwarded headers (from proxy/load balancer)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP in the chain
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    
    # Fallback to direct client IP
    if request.client:
        return request.client.host
    
    return "unknown"

def is_bot_request(request: Request) -> bool:
    """Check if request is from a bot/crawler"""
    user_agent = request.headers.get("User-Agent", "").lower()
    return any(bot in user_agent for bot in BOT_USER_AGENTS)

def check_rate_limit(ip: str, request: Request = None) -> tuple[bool, OptionalType[dict]]:
    """Check if IP is rate limited. Returns (allowed, cached_result)"""
    # Check for bots
    if request and is_bot_request(request):
        return False, None
    
    if ip == "unknown":
        return False, None
    
    # Check cache
    if ip in preview_cache:
        cached = preview_cache[ip]
        if datetime.utcnow() < cached['expires_at']:
            return True, cached['result']  # Return cached result
    
    return True, None

def set_rate_limit(ip: str, result: dict):
    """Store result in cache for 24 hours"""
    preview_cache[ip] = {
        'result': result,
        'expires_at': datetime.utcnow() + timedelta(hours=24)
    }
    # Clean old entries (simple cleanup, keep last 1000)
    if len(preview_cache) > 1000:
        now = datetime.utcnow()
        preview_cache.clear()  # Simple: clear all if too many (prevents memory leak)

# Add site access middleware (only does anything if SITE_ACCESS_PASSWORD is set)
app.add_middleware(SiteAccessMiddleware)

# Log site access protection status
if SITE_ACCESS_PASSWORD:
    print("🔒 Site access password protection is ENABLED")
else:
    print("🔓 Site access password protection is DISABLED (no SITE_ACCESS_PASSWORD set)")

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

# ============================================================================
# SITE ACCESS ROUTES (for temporary password protection)
# ============================================================================

@app.get("/access", response_class=HTMLResponse)
async def access_page(request: Request, error: str = None):
    """Serve the site access password form"""
    # If no password is set, redirect to home
    if not SITE_ACCESS_PASSWORD:
        return RedirectResponse(url="/", status_code=302)
    
    # If already authenticated, redirect to home
    if request.cookies.get("site_access_granted") == "true":
        return RedirectResponse(url="/", status_code=302)
    
    return templates.TemplateResponse("access.html", {
        "request": request,
        "error": error
    })

@app.post("/access")
async def access_submit(request: Request, password: str = Form(...)):
    """Handle site access password submission"""
    # If no password is set, redirect to home
    if not SITE_ACCESS_PASSWORD:
        return RedirectResponse(url="/", status_code=302)
    
    if password == SITE_ACCESS_PASSWORD:
        # Correct password - set cookie and redirect to home
        response = RedirectResponse(url="/", status_code=302)
        
        # Determine if we should use secure cookie (HTTPS)
        is_https = request.url.scheme == "https" or os.getenv("RENDER", "") == "true"
        
        response.set_cookie(
            key="site_access_granted",
            value="true",
            httponly=True,
            secure=is_https,
            samesite="lax",
            max_age=60 * 60 * 24 * 30  # 30 days
        )
        return response
    else:
        # Wrong password - show error
        return templates.TemplateResponse("access.html", {
            "request": request,
            "error": "Incorrect password. Please try again."
        }, status_code=401)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()
    print("Database initialized successfully")
    # Create test user if CREATE_TEST_USER env var is set
    init_test_data_if_needed()

# ============================================================================
# 404 ERROR HANDLER
# ============================================================================

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle 404 and other HTTP exceptions"""
    # If it's a 404, show custom 404 page
    if exc.status_code == 404:
        # Don't show 404 for static files or API endpoints
        path = request.url.path
        if path.startswith("/static/") or path.startswith("/api/"):
            # For API endpoints, return JSON error
            return Response(
                content=json.dumps({"detail": "Not found"}),
                status_code=404,
                media_type="application/json"
            )
        # For HTML pages, show custom 404 page
        return templates.TemplateResponse("404.html", {
            "request": request
        }, status_code=404)
    
    # For other HTTP exceptions, return default response
    return Response(
        content=json.dumps({"detail": exc.detail}),
        status_code=exc.status_code,
        media_type="application/json"
    )

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

@app.get("/patterns", response_class=HTMLResponse)
async def patterns_page(request: Request):
    """Serve the predictions/patterns page"""
    return templates.TemplateResponse("patterns.html", {"request": request})

@app.get("/ownpage", response_class=HTMLResponse)
async def ownpage(request: Request):
    """Serve the user profile page"""
    return templates.TemplateResponse("ownpage.html", {"request": request})

@app.get("/read", response_class=HTMLResponse)
async def read_page(request: Request):
    """Serve the study/blog page"""
    return templates.TemplateResponse("read.html", {"request": request})

@app.get("/membership", response_class=HTMLResponse)
async def membership_page(request: Request):
    """Serve the membership status page"""
    return templates.TemplateResponse("membership.html", {"request": request})

# ============================================================================
# Authentication Endpoints (Magic Link Only - No Passwords)
# ============================================================================

@app.post("/api/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user (Magic Link system - no password required).
    
    IMPORTANT: Birth data (birth_date, birth_time, birth_city) and zodiac_sign 
    are set ONCE during registration and CANNOT be changed later.
    The zodiac_sign is automatically calculated from birth_date.
    """
    # Check if user already exists
    existing_user = get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Calculate zodiac sign from birth date (IMMUTABLE after registration)
    zodiac_sign = None
    if user_data.birth_date:
        zodiac_sign = calculate_zodiac_sign(user_data.birth_date)
    
    # Create new user WITHOUT password (Magic Link only)
    new_user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        phone=user_data.phone,
        address=user_data.address,
        hashed_password=None,  # No password - Magic Link only
        # Birth data - IMMUTABLE after registration
        birth_date=user_data.birth_date,
        birth_time=user_data.birth_time,
        birth_city=user_data.birth_city,
        zodiac_sign=zodiac_sign,  # Auto-calculated, NEVER editable
        prediction_language=getattr(user_data, 'prediction_language', 'en') or 'en'
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@app.get("/api/admin/check-user/{email}")
async def admin_check_user(email: str, db: Session = Depends(get_db)):
    """
    Admin endpoint to check if a user exists (for debugging).
    In production, protect this with authentication.
    """
    user = get_user_by_email(db, email)
    if user:
        return {
            "exists": True,
            "email": user.email,
            "is_subscriber": user.is_subscriber,
            "zodiac_sign": user.zodiac_sign,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
    return {"exists": False, "email": email}

class PreviewRequest(BaseModel):
    zodiac_sign: str

@app.post("/api/preview-horoscope")
async def preview_horoscope(request: Request, data: PreviewRequest = Body(...)):
    """
    Generate a free preview horoscope for visitors.
    Rate limited: 1 per IP per 24 hours.
    Bot protection enabled.
    """
    # Get client IP
    client_ip = get_client_ip(request)
    
    # Check if bot
    if is_bot_request(request):
        raise HTTPException(
            status_code=403, 
            detail="Bot-pyynnöt eivät ole sallittuja",
            headers={"Content-Type": "application/json"}
        )
    
    # Check rate limit
    allowed, cached_result = check_rate_limit(client_ip, request)
    
    if not allowed:
        raise HTTPException(
            status_code=429, 
            detail="Ennuste on jo haettu tältä IP-osoitteelta viimeisen 24 tunnin aikana.",
            headers={"Content-Type": "application/json"}
        )
    
    # Return cached result if available
    if cached_result:
        return cached_result
    
    # Get zodiac sign from request body (data is a Pydantic model)
    zodiac_sign = data.zodiac_sign.strip()
    
    # Validate zodiac sign (normalize to handle case issues)
    valid_signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", 
                   "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
    
    if zodiac_sign not in valid_signs:
        raise HTTPException(
            status_code=400, 
            detail=f"Virheellinen horoskooppimerkki: {zodiac_sign}",
            headers={"Content-Type": "application/json"}
        )
    
    try:
        # Generate preview horoscope
        horoscope_text, lucky_number = gemini_client.generate_preview_horoscope(zodiac_sign)
        
        result = {
            "horoscope": horoscope_text,
            "lucky_number": lucky_number,
            "zodiac_sign": zodiac_sign,
            "generated_at": datetime.utcnow().isoformat()
        }
        
        # Cache result for 24 hours
        set_rate_limit(client_ip, result)
        
        return result
        
    except GeminiAPIError as e:
        print(f"Gemini API error in preview: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Ennusteen generointi epäonnistui. Yritä myöhemmin uudelleen.",
            headers={"Content-Type": "application/json"}
        )
    except Exception as e:
        print(f"Error generating preview horoscope: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500, 
            detail="Palvelinvirhe. Yritä myöhemmin uudelleen.",
            headers={"Content-Type": "application/json"}
        )

@app.post("/api/auth/magic-link", response_model=MagicLinkResponse)
async def request_magic_link(data: MagicLinkRequest, db: Session = Depends(get_db)):
    """
    Request a magic link to be sent to email.
    
    SECURITY:
    - Always returns the same message regardless of whether email exists
    - Only sends email if user exists in database
    - Token expires after 10 minutes
    - Token is single-use
    """
    print(f"🔐 Magic link requested for email: {data.email}")
    
    # Always return same message for security (don't reveal if email exists)
    response = MagicLinkResponse()
    
    # Check if user exists (case-insensitive search)
    user = db.query(User).filter(User.email.ilike(data.email)).first()
    
    if user:
        # Generate secure token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        
        # Create magic link token record
        magic_token = MagicLinkToken(
            token=token,
            user_id=user.id,
            expires_at=expires_at,
            used=False
        )
        db.add(magic_token)
        db.commit()
        
        # Send magic link email (in user's language)
        user_name = user.first_name or user.full_name or None
        user_lang = user.prediction_language or 'fi'
        email_service.send_magic_link(user.email, token, user_name, user_lang)
        
        print(f"✅ Magic link generated for {user.email} (lang: {user_lang})")
    else:
        # Don't reveal that email doesn't exist
        print(f"⚠️ Magic link requested for non-existent email: {data.email}")
    
    return response

@app.get("/magic-login", response_class=HTMLResponse)
async def magic_login_page(request: Request, token: str = None, db: Session = Depends(get_db)):
    """
    Validate magic link token and log in user.
    
    If valid: Set JWT cookie and redirect to dashboard
    If invalid: Show error page with option to request new link
    """
    if not token:
        return templates.TemplateResponse("magic-link-error.html", {
            "request": request,
            "error": "No token provided"
        })
    
    # Find token in database
    magic_token = db.query(MagicLinkToken).filter(
        MagicLinkToken.token == token
    ).first()
    
    # Check if token exists
    if not magic_token:
        return templates.TemplateResponse("magic-link-error.html", {
            "request": request,
            "error": "Invalid or expired link"
        })
    
    # Check if token is already used
    if magic_token.used:
        return templates.TemplateResponse("magic-link-error.html", {
            "request": request,
            "error": "This link has already been used"
        })
    
    # Check if token is expired
    if datetime.utcnow() > magic_token.expires_at:
        return templates.TemplateResponse("magic-link-error.html", {
            "request": request,
            "error": "This link has expired"
        })
    
    # Token is valid! Mark as used
    magic_token.used = True
    magic_token.used_at = datetime.utcnow()
    db.commit()
    
    # Get user
    user = db.query(User).filter(User.id == magic_token.user_id).first()
    
    if not user:
        return templates.TemplateResponse("magic-link-error.html", {
            "request": request,
            "error": "User not found"
        })
    
    # Create JWT access token
    access_token = create_access_token(data={"sub": user.email})
    
    # Create response with redirect to dashboard
    response = RedirectResponse(url="/dashboard", status_code=302)
    
    # Set JWT in HttpOnly secure cookie
    is_https = request.url.scheme == "https" or os.getenv("RENDER", "") == "true"
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=is_https,
        samesite="lax",
        max_age=60 * 60 * 24 * 7  # 7 days
    )
    
    # Also set a flag for frontend to know user is logged in
    response.set_cookie(
        key="logged_in",
        value="true",
        httponly=False,  # Frontend can read this
        secure=is_https,
        samesite="lax",
        max_age=60 * 60 * 24 * 7
    )
    
    print(f"✅ Magic link login successful for {user.email}")
    
    return response

@app.get("/logout")
async def logout(request: Request):
    """
    Logout user by clearing auth cookies.
    Redirects to home page.
    """
    response = RedirectResponse(url="/", status_code=302)
    
    # Clear auth cookies
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="logged_in")
    
    return response

@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information"""
    return current_user

@app.put("/api/auth/profile", response_model=UserResponse)
async def update_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update user profile information.
    
    IMPORTANT: This endpoint can only update editable fields:
    - first_name, last_name, phone, address, full_name, prediction_language
    
    The following fields are IMMUTABLE and CANNOT be changed:
    - birth_date (set at registration)
    - birth_city (set at registration)
    - zodiac_sign (auto-calculated from birth_date, never editable)
    
    Birth time can be added/updated for more precise predictions.
    Prediction language determines the language for all horoscope predictions.
    """
    # Only update allowed fields
    if profile_data.first_name is not None:
        current_user.first_name = profile_data.first_name
    if profile_data.last_name is not None:
        current_user.last_name = profile_data.last_name
    if profile_data.phone is not None:
        current_user.phone = profile_data.phone
    if profile_data.address is not None:
        current_user.address = profile_data.address
    if profile_data.full_name is not None:
        current_user.full_name = profile_data.full_name
    # Birth time can be added/updated for more precise predictions
    if profile_data.birth_time is not None:
        current_user.birth_time = profile_data.birth_time
    # Prediction language - determines language for all horoscopes
    if profile_data.prediction_language is not None:
        # Validate language code (common languages)
        valid_languages = ['fi', 'en', 'sv', 'no', 'da', 'de', 'fr', 'es', 'it']
        if profile_data.prediction_language in valid_languages:
            current_user.prediction_language = profile_data.prediction_language
        else:
            # Default to 'fi' if invalid
            current_user.prediction_language = 'fi'
    
    db.commit()
    db.refresh(current_user)
    
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
# Horoscope Endpoints with Rate Limiting
# ============================================================================

# Rate limit intervals for each prediction type
RATE_LIMIT_INTERVALS = {
    "daily": timedelta(hours=24),
    "weekly": timedelta(days=7),
    "monthly": timedelta(days=30)
}

def check_rate_limit(db: Session, user_id: int, prediction_type: str) -> dict:
    """
    Check if user can generate a new horoscope of the given type.
    
    IMPORTANT: First prediction of each type is ALWAYS allowed!
    After the first prediction, rate limits apply:
    - Daily: 24 hours between predictions
    - Weekly: 7 days between predictions
    - Monthly: 30 days between predictions
    
    Returns dict with:
    - can_generate: boolean
    - is_first: boolean (true if this would be their first of this type)
    - next_available_at: ISO timestamp or null
    - last_generated_at: ISO timestamp or null
    """
    interval = RATE_LIMIT_INTERVALS.get(prediction_type, timedelta(hours=24))
    
    # Get the latest horoscope of this type for this user
    latest = db.query(Horoscope).filter(
        Horoscope.user_id == user_id,
        Horoscope.prediction_type == prediction_type
    ).order_by(Horoscope.created_at.desc()).first()
    
    now = datetime.utcnow()
    
    # FIRST PREDICTION IS ALWAYS FREE!
    # If user has never generated this type, allow immediately
    if not latest:
        return {
            "can_generate": True,
            "is_first": True,
            "next_available_at": None,
            "last_generated_at": None,
            "latest_horoscope_id": None,
            "message": f"Generate your first {prediction_type} prediction!"
        }
    
    # User has generated before - check rate limit
    next_allowed = latest.created_at + interval
    
    if now < next_allowed:
        # Still within rate limit period
        return {
            "can_generate": False,
            "is_first": False,
            "next_available_at": next_allowed.isoformat(),
            "last_generated_at": latest.created_at.isoformat(),
            "latest_horoscope_id": latest.id,
            "message": f"Next {prediction_type} available after rate limit"
        }
    
    # Rate limit has passed
    return {
        "can_generate": True,
        "is_first": False,
        "next_available_at": None,
        "last_generated_at": latest.created_at.isoformat(),
        "latest_horoscope_id": latest.id,
        "message": f"Ready for new {prediction_type} prediction"
    }

@app.get("/api/horoscopes/status")
async def get_horoscope_status(
    prediction_type: str = "daily",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Check if user can generate a new horoscope of the specified type.
    Returns rate limit status and next available time.
    """
    if prediction_type not in RATE_LIMIT_INTERVALS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid prediction_type. Must be one of: {list(RATE_LIMIT_INTERVALS.keys())}"
        )
    
    status_info = check_rate_limit(db, current_user.id, prediction_type)
    
    # Add interval info
    interval = RATE_LIMIT_INTERVALS[prediction_type]
    status_info["interval_hours"] = interval.total_seconds() / 3600
    status_info["prediction_type"] = prediction_type
    
    return status_info

@app.get("/api/horoscopes/status/all")
async def get_all_horoscope_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get rate limit status for all prediction types at once.
    """
    result = {}
    for prediction_type in RATE_LIMIT_INTERVALS.keys():
        status_info = check_rate_limit(db, current_user.id, prediction_type)
        interval = RATE_LIMIT_INTERVALS[prediction_type]
        status_info["interval_hours"] = interval.total_seconds() / 3600
        result[prediction_type] = status_info
    
    return result

@app.post("/api/horoscopes/generate")
async def generate_horoscope(
    horoscope_data: HoroscopeCreate,
    current_user: User = Depends(get_current_subscriber),
    db: Session = Depends(get_db)
):
    """
    Generate a new horoscope prediction (subscribers only).
    
    Rate limits:
    - daily: once every 24 hours
    - weekly: once every 7 days
    - monthly: once every 30 days
    
    Returns:
    - can_generate: boolean
    - next_available_at: ISO timestamp if rate limited
    - content: AI generated text if allowed
    - horoscope: full horoscope object if allowed
    """
    prediction_type = horoscope_data.prediction_type
    
    # Check rate limit
    rate_status = check_rate_limit(db, current_user.id, prediction_type)
    
    if not rate_status["can_generate"]:
        return {
            "can_generate": False,
            "next_available_at": rate_status["next_available_at"],
            "content": None,
            "horoscope": None,
            "message": f"You can generate a new {prediction_type} horoscope after {rate_status['next_available_at']}"
        }
    
    # Use user's profile zodiac sign if available (overrides request)
    zodiac_sign = current_user.zodiac_sign or horoscope_data.zodiac_sign
    
    if not zodiac_sign:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No zodiac sign available. Please add your birth date in your profile."
        )
    
    # Calculate user's age from birth_date
    age = None
    if current_user.birth_date:
        try:
            birth_date = datetime.strptime(current_user.birth_date, "%Y-%m-%d").date()
            today = datetime.now().date()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        except (ValueError, TypeError):
            age = None
    
    # Build user profile data for personalized predictions
    user_profile = {
        "birth_date": current_user.birth_date,
        "birth_time": current_user.birth_time,
        "birth_city": current_user.birth_city,
        "zodiac_sign": zodiac_sign,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "email": current_user.email,
        "prediction_language": getattr(current_user, 'prediction_language', 'fi') or 'fi',
        "age": age  # Age is required for age-specific voice in Gemini rules
    }
    
    # Generate horoscope using Gemini with user's profile data
    # NO FALLBACKS - Gemini MUST generate the horoscope directly
    try:
        content, raw_data = gemini_client.generate_horoscope(
            zodiac_sign=zodiac_sign,
            prediction_type=prediction_type,
            user_profile=user_profile
        )
    except GeminiAPIError as e:
        print(f"❌ Gemini API Error: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "error": "horoscope_generation_failed",
                "message": "Unable to generate horoscope at this time. Please try again later.",
                "technical_details": str(e)
            }
        )
    
    # Save to database - always use the user's profile zodiac_sign
    new_horoscope = Horoscope(
        user_id=current_user.id,
        zodiac_sign=zodiac_sign,
        prediction_type=prediction_type,
        content=content,
        raw_data=json.dumps(raw_data),
        prediction_date=datetime.utcnow()
    )
    
    db.add(new_horoscope)
    db.commit()
    db.refresh(new_horoscope)
    
    # Calculate next available time
    interval = RATE_LIMIT_INTERVALS[prediction_type]
    next_available = new_horoscope.created_at + interval
    
    return {
        "can_generate": True,
        "next_available_at": next_available.isoformat(),
        "content": content,
        "horoscope": {
            "id": new_horoscope.id,
            "zodiac_sign": new_horoscope.zodiac_sign,
            "prediction_type": new_horoscope.prediction_type,
            "content": new_horoscope.content,
            "raw_data": new_horoscope.raw_data,
            "created_at": new_horoscope.created_at.isoformat(),
            "prediction_date": new_horoscope.prediction_date.isoformat()
        }
    }

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

@app.get("/api/horoscopes", response_model=list[HoroscopeResponse])
async def get_all_horoscopes(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all horoscopes for current user, newest first.
    This endpoint is used by the /patterns page to display all predictions.
    """
    horoscopes = db.query(Horoscope).filter(
        Horoscope.user_id == current_user.id
    ).order_by(Horoscope.created_at.desc()).all()
    
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

@app.get("/api/subscription")
async def get_subscription(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user's subscription (returns None if no subscription)"""
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    ).first()
    
    if not subscription:
        return None
    
    return {
        "id": subscription.id,
        "status": subscription.status,
        "current_period_start": subscription.current_period_start,
        "current_period_end": subscription.current_period_end
    }
    
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
