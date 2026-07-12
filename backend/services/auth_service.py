from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from backend.core.database import get_db
import os

# JWT Settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours as per requirements

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_comprehensive_jwt_token(user, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT token with comprehensive user claims"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Get user permissions from role
    permissions = []
    if user.role and hasattr(user.role, 'permissions') and user.role.permissions:
        # Extract all permissions from role.permissions dict
        for model_name, model_perms in user.role.permissions.items():
            for action, allowed in model_perms.items():
                if allowed:
                    permissions.append(f"{model_name}.{action}")
    
    # Build comprehensive claims
    claims = {
        "sub": user.email,  # Subject (standard JWT claim)
        "user_id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role.name if user.role else "user",
        "permissions": permissions,
        "preferences": {
            "show_notification_toasts": user.show_notification_toasts,
            "theme": getattr(user, 'theme', 'light')
        },
        "is_active": user.is_active,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    
    return jwt.encode(claims, SECRET_KEY, algorithm=ALGORITHM)

def validate_jwt_token(token: str) -> Dict[str, Any]:
    """Validate JWT token and return comprehensive claims"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def extract_user_claims_from_jwt(token: str) -> Dict[str, Any]:
    """Extract user claims from JWT token for authorization"""
    payload = validate_jwt_token(token)
    
    return {
        "user_id": payload.get("user_id"),
        "email": payload.get("sub"),
        "full_name": payload.get("full_name"),
        "role": payload.get("role"),
        "permissions": payload.get("permissions", []),
        "preferences": payload.get("preferences", {}),
        "is_active": payload.get("is_active", True)
    }

def verify_token(token: str):
    """Verify JWT token and return user email"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email: str = payload.get("sub")
        if user_email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user_email
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user_from_jwt(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Get current user from JWT token with comprehensive validation"""
    from backend.models.user import User
    
    try:
        # Validate token and extract claims
        claims = validate_jwt_token(token)
        user_email = claims.get("sub")
        
        if user_email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user from database to ensure current data
        user = db.query(User).filter(User.email == user_email).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify user is still active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def refresh_jwt_token(current_user, db: Session) -> str:
    """Refresh JWT token with updated user data"""
    # Refresh user data from database
    db.refresh(current_user)
    
    # Generate new token with fresh data
    return create_comprehensive_jwt_token(current_user)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Get current user from JWT token"""
    from backend.models.user import User
    
    try:
        user_email = verify_token(token)
        user = db.query(User).filter(User.email == user_email).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
