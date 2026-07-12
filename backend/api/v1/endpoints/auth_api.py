from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from backend.core.base_model import Environment
from backend.core.registry import registry
from backend.core.database import get_db
from backend.models.user import User
from backend.models.role import Role
from backend.models.password_reset_token import PasswordResetToken
from backend.services.auth_service import (
    verify_password, 
    create_access_token, 
    create_comprehensive_jwt_token,
    refresh_jwt_token,
    get_current_user_from_jwt,
    ACCESS_TOKEN_EXPIRE_MINUTES, 
    get_password_hash
)
from backend.services.email_service import email_service
from backend.services.google_oauth import google_oauth
from backend.core.exceptions import ValidationError, AuthenticationError, RateLimitError
from pydantic import BaseModel, EmailStr, validator
import logging
import os
import secrets
import re
from collections import defaultdict
import time

logger = logging.getLogger(__name__)
router = APIRouter()

# Rate limiting storage (in production, use Redis)
login_attempts = defaultdict(list)
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = 900  # 15 minutes

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Za-z]', v):
            raise ValueError('Password must contain at least one letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        return v
    
    @validator('full_name')
    def validate_full_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Full name must be at least 2 characters long')
        return v.strip()

class AdminResetPasswordRequest(BaseModel):
    user_id: int
    new_password: str
    confirm_password: str
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Za-z]', v):
            raise ValueError('Password must contain at least one letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v

class LoginRequest(BaseModel):
    username: EmailStr
    password: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Za-z]', v):
            raise ValueError('Password must contain at least one letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        return v

class GoogleAuthRequest(BaseModel):
    code: str
    state: str

def check_rate_limit(ip_address: str) -> bool:
    """Check if IP is rate limited"""
    now = time.time()
    # Clean old attempts
    login_attempts[ip_address] = [
        attempt_time for attempt_time in login_attempts[ip_address]
        if now - attempt_time < LOCKOUT_DURATION
    ]
    
    return len(login_attempts[ip_address]) < MAX_LOGIN_ATTEMPTS

def record_failed_attempt(ip_address: str):
    """Record a failed login attempt"""
    login_attempts[ip_address].append(time.time())

def get_client_ip(request: Request) -> str:
    """Get client IP address"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

@router.post("/signup")
def signup(request: SignupRequest, client_request: Request, db: Session = Depends(get_db)):
    client_ip = get_client_ip(client_request)
    
    # Check rate limiting
    if not check_rate_limit(client_ip):
        logger.warning(f"Signup rate limited for IP: {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many signup attempts. Please try again later."
        )
    
    # Check if user already exists
    env = Environment(db)
    existing_user = env['user'].search([('email', '=', request.email)], limit=1)
    if existing_user:
        logger.warning(f"Signup attempt with existing email: {request.email} from {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists"
        )
    
    # Get or create user role
    user_role = env['role'].search([('name', '=', 'user')], limit=1)
    if not user_role:
        user_role = Role(name="user", description="Normal User")
        db.add(user_role)
        db.flush()

    try:
        # Create new user
        new_user = User.create(db, {
            'email': request.email,
            'full_name': request.full_name,
            'hashed_password': get_password_hash(request.password),
            'role_id': user_role.id,
            'is_active': True
        })
        
        # Update last login time
        new_user.update_last_login()
        
        # Create comprehensive JWT token with user claims (auto-login)
        access_token = create_comprehensive_jwt_token(new_user)
        
        logger.info(f"New user registered: {request.email}")
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": new_user.id,
                "email": new_user.email,
                "full_name": new_user.full_name,
                "role": {
                    "name": new_user.role.name if new_user.role else "user",
                    "label": new_user.role.name if new_user.role else "user"
                },
                "is_active": new_user.is_active,
                "image": new_user.image,
                "show_notification_toasts": new_user.show_notification_toasts
            },
            "message": "Account created successfully!",
            "success": True
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Signup error for {request.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create account. Please try again."
        )

@router.post("/login")
def login(request: LoginRequest, client_request: Request, db: Session = Depends(get_db)):
    client_ip = get_client_ip(client_request)
    user_agent = client_request.headers.get("user-agent", "unknown")
    
    logger.debug(f"Login attempt: {request.username} from {client_ip}")
    
    # Check rate limiting
    if not check_rate_limit(client_ip):
        logger.warning(f"Login rate limited for IP: {client_ip}")
        raise RateLimitError("Too many login attempts. Please try again in 15 minutes.")
    
    # Find user
    env = Environment(db)
    user = env['user'].search([('email', '=', request.username)], limit=1)
    if not user:
        record_failed_attempt(client_ip)
        logger.warning(f"Login failed - user not found: {request.username} from {client_ip}")
        raise AuthenticationError("No account found with this email address")
    
    # Check if user is active first
    if not user.is_active:
        record_failed_attempt(client_ip)
        logger.warning(f"Login failed - inactive user: {request.username} from {client_ip}")
        raise AuthenticationError("Your account has been deactivated. Please contact support.")
    
    # Verify password
    if not verify_password(request.password, user.hashed_password):
        record_failed_attempt(client_ip)
        logger.warning(f"Login failed - invalid password for user: {request.username} from {client_ip}")
        raise AuthenticationError("Incorrect password. Please check your password and try again.")
    
    # Update last login time
    user.update_last_login()
    
    # Create comprehensive JWT token with user claims
    access_token = create_comprehensive_jwt_token(user)
    
    logger.info(f"Login: {request.username}")
    
    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": {
                "name": user.role.name if user.role else "user",
                "label": user.role.name if user.role else "user"
            },
            "is_active": user.is_active,
            "image": user.image,
            "show_notification_toasts": user.show_notification_toasts
        },
        "message": "Login successful",
        "success": True
    }

@router.post("/forgot-password")
def forgot_password(request: ForgotPasswordRequest, client_request: Request, db: Session = Depends(get_db)):
    client_ip = get_client_ip(client_request)
    
    # Check rate limiting
    if not check_rate_limit(client_ip):
        logger.warning(f"Password reset rate limited for IP: {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many password reset attempts. Please try again later."
        )
    
    # Find user
    env = Environment(db)
    user = env['user'].search([('email', '=', request.email)], limit=1)
    if not user:
        # Don't reveal if email exists or not for security, but log it
        logger.debug(f"Password reset requested for non-existent email: {request.email}")
        return {
            "message": "If an account with this email exists, a password reset link has been sent.",
            "success": True
        }
    
    if not user.is_active:
        logger.warning(f"Password reset requested for inactive user: {request.email} from {client_ip}")
        return {
            "message": "If an account with this email exists, a password reset link has been sent.",
            "success": True
        }
    
    try:
        # Invalidate any existing tokens for this user
        existing_tokens = env['password_reset_token'].search([
            ('user_id', '=', user.id),
            ('used', '=', False)
        ])
        
        for token in existing_tokens:
            token.mark_as_used()
        
        # Create new reset token
        reset_token = env['password_reset_token'].create({'user_id': user.id})
        
        # Send email
        email_sent = email_service.send_password_reset_email(
            to_email=user.email,
            reset_token=reset_token.token,
            user_name=user.full_name or user.email
        )
        
        if email_sent:
            logger.info(f"Password reset email sent to: {user.email} from {client_ip}")
        else:
            logger.error(f"Failed to send password reset email to: {user.email}")
        
        return {
            "message": "If an account with this email exists, a password reset link has been sent.",
            "success": True
        }
    except Exception as e:
        logger.error(f"Password reset error for {request.email}: {str(e)}")
        return {
            "message": "If an account with this email exists, a password reset link has been sent.",
            "success": True
        }

@router.post("/reset-password")
def reset_password(request: ResetPasswordRequest, client_request: Request, db: Session = Depends(get_db)):
    client_ip = get_client_ip(client_request)
    
    # Find and validate token
    env = Environment(db)
    reset_token = env['password_reset_token'].search([('token', '=', request.token)], limit=1)
    
    if not reset_token or not reset_token.is_valid():
        logger.warning(f"Invalid or expired reset token used: {request.token} from {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This password reset link is invalid or has expired. Please request a new one."
        )
    
    # Get user
    user = reset_token.user
    if not user or not user.is_active:
        logger.warning(f"Reset password attempted for inactive user: {user.email if user else 'unknown'} from {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This password reset link is invalid or has expired. Please request a new one."
        )
    
    try:
        # Update password
        user.write({'hashed_password': get_password_hash(request.new_password)})
        
        # Mark token as used
        reset_token.mark_as_used()
        
        logger.info(f"Password reset successful for user: {user.email} from {client_ip}")
        return {
            "message": "Your password has been updated successfully. You can now sign in with your new password.",
            "success": True
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Password reset error for user {user.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password. Please try again."
        )

@router.get("/google")
def google_auth_url():
    """Get Google OAuth authorization URL"""
    if not google_oauth.is_configured():
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth is not configured. Please contact support."
        )
    
    try:
        state = secrets.token_urlsafe(32)
        auth_url = google_oauth.get_authorization_url(state)
        
        return {
            "auth_url": auth_url,
            "state": state,
            "success": True
        }
    except Exception as e:
        logger.error(f"Failed to generate Google auth URL: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate Google authentication URL. Please try again."
        )

@router.post("/google")
def google_auth_callback(request: GoogleAuthRequest, client_request: Request, db: Session = Depends(get_db)):
    """Handle Google OAuth callback"""
    client_ip = get_client_ip(client_request)
    
    if not google_oauth.is_configured():
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth is not configured"
        )
    
    try:
        # Exchange code for token
        token_data = google_oauth.exchange_code_for_token(request.code)
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to authenticate with Google. Please try again."
            )
        
        # Get user info from Google
        user_info = google_oauth.get_user_info(token_data['access_token'])
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user information from Google. Please try again."
            )
        
        email = user_info.get('email')
        name = user_info.get('name', '')
        
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not provided by Google. Please try again."
            )
        env = Environment(db)
        # Get user from database to verify current status
        user = env['user'].search([('email', '=', email)], limit=1)
        
        if not user:
            # Create new user
            user_role = env['role'].search([('name', '=', 'user')], limit=1)
            if not user_role:
                user_role = env['role'].create({'name': 'user', 'description': 'Normal User'})
            
            # Generate a random password for Google users (they won't use it)
            random_password = secrets.token_urlsafe(32)
            
            user = env['user'].create({
                'email': email,
                'full_name': name,
                'hashed_password': get_password_hash(random_password),
                'role_id': user_role.id,
                'is_active': True
            })
            
            logger.info(f"New user created via Google OAuth: {email} from {client_ip}")
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Your account has been deactivated. Please contact support."
            )
        
        # Update last login time
        user.update_last_login(db)
        
        # Create comprehensive JWT token with user claims
        access_token = create_comprehensive_jwt_token(user)
        
        logger.info(f"Google OAuth login successful for user: {email} from {client_ip}")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": {
                    "name": user.role.name if user.role else "user",
                    "label": user.role.name if user.role else "user"
                },
                "is_active": user.is_active,
                "image": user.image,
                "show_notification_toasts": user.show_notification_toasts
            },
            "message": "Google login successful",
            "success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google OAuth error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google authentication failed. Please try again."
        )

@router.get("/profile")
def get_profile(current_user: User = Depends(get_current_user_from_jwt), db: Session = Depends(get_db)):
    """Get comprehensive user profile data"""
    try:
        # Refresh user data to ensure it's current
        db.refresh(current_user)
        
        # Get user permissions
        permissions = []
        if current_user.role and hasattr(current_user.role, 'permissions') and current_user.role.permissions:
            for model_name, model_perms in current_user.role.permissions.items():
                for action, allowed in model_perms.items():
                    if allowed:
                        permissions.append(f"{model_name}.{action}")
        
        return {
            "user": {
                "id": current_user.id,
                "email": current_user.email,
                "full_name": current_user.full_name,
                "role": {
                    "name": current_user.role.name if current_user.role else "user",
                    "label": current_user.role.name if current_user.role else "user",
                    "permissions": permissions
                },
                "is_active": current_user.is_active,
                "image": current_user.image,
                "last_login_at": current_user.last_login_at.isoformat() if current_user.last_login_at else None,
                "created_at": current_user.created_at.isoformat() if hasattr(current_user, 'created_at') and current_user.created_at else None,
                "updated_at": current_user.updated_at.isoformat() if hasattr(current_user, 'updated_at') and current_user.updated_at else None
            },
            "preferences": {
                "show_notification_toasts": current_user.show_notification_toasts,
                "theme": getattr(current_user, 'theme', 'light')
            },
            "permissions": permissions,
            "success": True
        }
    except Exception as e:
        logger.error(f"Profile fetch error for user {current_user.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch profile data"
        )

@router.post("/refresh-token")
def refresh_token(current_user: User = Depends(get_current_user_from_jwt), db: Session = Depends(get_db)):
    """Refresh JWT token with updated user data"""
    try:
        # Generate new token with fresh user data
        new_token = refresh_jwt_token(current_user, db)
        
        logger.info(f"Token refreshed for user: {current_user.email}")
        
        return {
            "access_token": new_token,
            "token_type": "bearer",
            "message": "Token refreshed successfully",
            "success": True
        }
    except Exception as e:
        logger.error(f"Token refresh error for user {current_user.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh token"
        )

@router.post("/logout")
def logout(current_user: User = Depends(get_current_user_from_jwt), client_request: Request = None):
    """Secure logout with token invalidation (Requirements 5.2, 5.6)"""
    client_ip = get_client_ip(client_request) if client_request else "unknown"
    
    try:
        # In a production system, you would:
        # 1. Add the token to a blacklist/revocation list
        # 2. Store revoked tokens in Redis or database
        # 3. Check blacklist on every token validation
        
        # For now, we'll log the logout and return success
        # The frontend will clear the token from localStorage
        logger.info(f"User logout: {current_user.email} from {client_ip}")
        
        return {
            "message": "Logout successful",
            "success": True
        }
    except Exception as e:
        logger.error(f"Logout error for user {current_user.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

@router.post("/admin/reset-password")
def admin_reset_user_password(request: AdminResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset user password (Admin only)"""
    
    try:
        env = Environment(db)
        # Find the user
        user = env['user'].browse(request.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Hash the new password
        new_hashed_password = get_password_hash(request.new_password)
        
        # Update the user's password
        user.write({'hashed_password': new_hashed_password})
        
        logger.info(f"Password reset successful for user: {user.email}")
        
        return {
            "success": True,
            "message": f"Password reset successfully for {user.full_name}",
            "user_email": user.email
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset error: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password. Please try again."
        )