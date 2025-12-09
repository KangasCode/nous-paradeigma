"""
Authentication and authorization utilities (Magic Link system - no passwords)
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import os

from database import get_db
from models import User
from schemas import TokenData

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Password hashing (kept for backwards compatibility)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme - optional (we also check cookies)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/magic-link", auto_error=False)

# HTTP Bearer scheme for Authorization header
http_bearer = HTTPBearer(auto_error=False)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash (deprecated - kept for migration)"""
    if not hashed_password:
        return False
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password (deprecated - kept for migration)"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email"""
    return db.query(User).filter(User.email == email).first()

def decode_token(token: str) -> Optional[str]:
    """Decode JWT token and return email if valid"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        return email
    except JWTError:
        return None

async def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    bearer: HTTPAuthorizationCredentials = Depends(http_bearer),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token.
    
    Token can come from:
    1. Authorization header (Bearer token) - for API calls
    2. HttpOnly cookie (access_token) - for browser requests
    3. localStorage token passed in header - for legacy support
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    jwt_token = None
    
    # 1. Check Bearer token from Authorization header
    if bearer and bearer.credentials:
        jwt_token = bearer.credentials
    
    # 2. Check OAuth2 token
    elif token:
        jwt_token = token
    
    # 3. Check HttpOnly cookie
    else:
        jwt_token = request.cookies.get("access_token")
    
    if not jwt_token:
        raise credentials_exception
    
    # Decode token
    email = decode_token(jwt_token)
    if not email:
        raise credentials_exception
    
    # Get user
    user = get_user_by_email(db, email)
    if user is None:
        raise credentials_exception
    
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_subscriber(current_user: User = Depends(get_current_active_user)) -> User:
    """Get current user and verify they are a subscriber"""
    if not current_user.is_subscriber:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Active subscription required to access this resource"
        )
    return current_user


