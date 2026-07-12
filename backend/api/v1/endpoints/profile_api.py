from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, validator
from typing import Optional, Dict, Any, List
from backend.core.database import get_db
from backend.core.websocket_manager import get_websocket_manager
from backend.services.auth_service import get_current_user_from_jwt, get_password_hash, verify_password
from backend.services.user_sync_service import get_user_sync_service
from backend.models.user import User
import re
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    
    @validator('full_name')
    def validate_full_name(cls, v):
        if v is not None and len(v.strip()) < 2:
            raise ValueError('Full name must be at least 2 characters long')
        return v.strip() if v else v

class UpdatePreferencesRequest(BaseModel):
    preferences: Dict[str, Any]

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Za-z]', v):
            raise ValueError('Password must contain at least one letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v

@router.get("/profile")
def get_profile(current_user: User = Depends(get_current_user_from_jwt), db: Session = Depends(get_db)):
    """Get current user's profile information"""
    try:
        # Refresh user data from database
        db.refresh(current_user)
        
        # Get user permissions
        permissions = []
        if current_user.role:
            permissions = current_user.role.permissions or []
        
        profile_data = {
            "id": current_user.id,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "is_active": current_user.is_active,
            "role": {
                "id": current_user.role.id if current_user.role else None,
                "name": current_user.role.name if current_user.role else "No Role",
                "description": current_user.role.description if current_user.role else "",
                "permissions": permissions
            },

            "image": current_user.image,
            "last_login_at": current_user.last_login_at.isoformat() if current_user.last_login_at else None,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
            "preferences": {
                "show_notification_toasts": current_user.show_notification_toasts,
                "theme": getattr(current_user, 'theme', 'light'),
                "timezone_id": getattr(current_user, 'timezone_id', None)
            }
        }
        
        return {
            "success": True,
            "data": profile_data
        }
        
    except Exception as e:
        logger.error(f"Error fetching profile for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch profile information"
        )

@router.put("/profile")
async def update_profile(
    request: UpdateProfileRequest,
    current_user: User = Depends(get_current_user_from_jwt),
    db: Session = Depends(get_db)
):
    """Update current user's profile information"""
    try:
        updated_fields = {}
        
        # Update profile information
        if request.full_name is not None:
            current_user.full_name = request.full_name
            updated_fields['full_name'] = request.full_name
        
        # Update preferences if provided
        if request.preferences is not None:
            for key, value in request.preferences.items():
                if key == 'show_notification_toasts':
                    current_user.show_notification_toasts = bool(value)
                    updated_fields['show_notification_toasts'] = bool(value)
                elif key == 'theme':
                    if value in ['light', 'dark']:
                        current_user.theme = value
                        updated_fields['theme'] = value
                elif key == 'timezone_id':
                    # Validate timezone_id exists
                    if value:
                        current_user.timezone_id = int(value)
                        updated_fields['timezone_id'] = int(value)
        
        db.commit()
        db.refresh(current_user)
        
        logger.debug(f"Profile updated for user {current_user.id}: {list(updated_fields.keys())}")
        
        # Broadcast user data update to all user's WebSocket connections
        try:
            from backend.core.websocket_manager import get_websocket_manager
            from backend.services.user_sync_service import get_user_sync_service
            
            websocket_manager = get_websocket_manager()
            user_sync_service = get_user_sync_service(websocket_manager)
            
            if updated_fields:
                # Broadcast general user data update
                await user_sync_service.broadcast_user_data_update(
                    current_user.id, 
                    updated_fields
                )
                
                # If preferences were updated, send specific preference update
                if request.preferences:
                    await user_sync_service.broadcast_user_preferences_update(
                        current_user.id,
                        request.preferences
                    )
                    
        except Exception as e:
            logger.warning(f"Failed to broadcast user data update: {e}")
            # Don't fail the request if broadcasting fails
        
        return {
            "success": True,
            "message": "Profile updated successfully",
            "data": {
                "id": current_user.id,
                "email": current_user.email,
                "full_name": current_user.full_name,
                "preferences": {
                    "show_notification_toasts": current_user.show_notification_toasts,
                    "theme": getattr(current_user, 'theme', 'light'),
                    "timezone_id": getattr(current_user, 'timezone_id', None)
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating profile for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )

@router.patch("/profile")
async def patch_profile(
    request: UpdatePreferencesRequest,
    current_user: User = Depends(get_current_user_from_jwt),
    db: Session = Depends(get_db)
):
    """Update user preferences (PATCH method for partial updates)"""
    try:
        updated_preferences = {}
        
        # Update preferences
        for key, value in request.preferences.items():
            if key == 'show_notification_toasts':
                current_user.show_notification_toasts = bool(value)
                updated_preferences['show_notification_toasts'] = bool(value)
            elif key == 'theme':
                if value in ['light', 'dark']:
                    current_user.theme = value
                    updated_preferences['theme'] = value
            elif key == 'timezone_id':
                # Validate timezone_id exists
                if value:
                    current_user.timezone_id = int(value)
                    updated_preferences['timezone_id'] = int(value)
        
        db.commit()
        db.refresh(current_user)
        
        logger.debug(f"Preferences updated for user {current_user.id}: {list(updated_preferences.keys())}")
        
        # Broadcast preference update to all user's WebSocket connections
        try:
            from backend.core.websocket_manager import get_websocket_manager
            from backend.services.user_sync_service import get_user_sync_service
            
            websocket_manager = get_websocket_manager()
            user_sync_service = get_user_sync_service(websocket_manager)
            
            if updated_preferences:
                await user_sync_service.broadcast_user_preferences_update(
                    current_user.id,
                    updated_preferences
                )
                    
        except Exception as e:
            logger.warning(f"Failed to broadcast preference update: {e}")
            # Don't fail the request if broadcasting fails
        
        return {
            "success": True,
            "message": "Preferences updated successfully",
            "data": {
                "preferences": updated_preferences
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating preferences for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update preferences"
        )

@router.put("/profile/password")
def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user_from_jwt),
    db: Session = Depends(get_db)
):
    """Change current user's password"""
    try:
        # Verify current password
        if not verify_password(request.current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Update password
        current_user.hashed_password = get_password_hash(request.new_password)
        
        db.commit()
        
        logger.debug(f"Password changed for user {current_user.id}")
        
        return {
            "success": True,
            "message": "Password changed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error changing password for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )

@router.put("/profile/image")
async def update_profile_image(
    image_data: dict,
    current_user: User = Depends(get_current_user_from_jwt),
    db: Session = Depends(get_db)
):
    """Update current user's profile image"""
    try:
        # Update profile image
        current_user.image = image_data.get('image')
        
        db.commit()
        
        logger.debug(f"Profile image updated for user {current_user.id}")
        
        # Broadcast user data update to all user's WebSocket connections
        try:
            from backend.core.websocket_manager import get_websocket_manager
            from backend.services.user_sync_service import get_user_sync_service
            
            websocket_manager = get_websocket_manager()
            user_sync_service = get_user_sync_service(websocket_manager)
            
            await user_sync_service.broadcast_user_data_update(
                current_user.id, 
                {'image': current_user.image}
            )
                    
        except Exception as e:
            logger.warning(f"Failed to broadcast profile image update: {e}")
            # Don't fail the request if broadcasting fails
        
        return {
            "success": True,
            "message": "Profile image updated successfully"
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating profile image for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile image"
        )