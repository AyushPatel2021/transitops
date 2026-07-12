"""
Notification API Endpoints

This module provides REST API endpoints for notification management including:
- GET /notifications - Retrieve user's notifications
- POST /notifications/{id}/read - Mark specific notification as read
- POST /notifications/read-all - Mark all notifications as read
- WebSocket /ws/notifications - Real-time notification delivery
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from backend.core.database import get_db
from backend.models.notification import Notification
from backend.models.user import User
from backend.services.notification_service import NotificationService, get_notification_service
from backend.services.auth_service import (
    SECRET_KEY, 
    ALGORITHM, 
    get_current_user_from_jwt, 
    validate_jwt_token, 
    extract_user_claims_from_jwt
)
from backend.core.websocket_manager import get_websocket_manager, WebSocketManager
from backend.core.exceptions import AuthenticationError, ValidationError
from backend.services.notification_cleanup_service import get_cleanup_service
from backend.core.background_scheduler import get_scheduler
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


# Request models
class CreateNotificationRequest(BaseModel):
    title: str
    message: str
    type: str = "info"
    user_id: Optional[int] = None  # If None, sends to current user


# Pydantic models for request/response
class NotificationResponse(BaseModel):
    id: int
    title: str
    message: str
    type: str
    read: bool
    read_at: Optional[str] = None
    action_type: Optional[str] = None
    action_target: Optional[str] = None
    action_params: Optional[dict] = None
    created_at: str
    expires_at: Optional[str] = None

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    notifications: List[NotificationResponse]
    total: int
    unread_count: int


class MarkReadResponse(BaseModel):
    success: bool
    message: str
    notification_id: int


class MarkAllReadResponse(BaseModel):
    success: bool
    message: str
    marked_count: int


class CleanupStatsResponse(BaseModel):
    counts: dict
    cutoff_dates: dict
    config: dict


class CleanupResultResponse(BaseModel):
    success: bool
    total_deleted: int
    categories: dict
    execution_time: float
    vacuum_run: bool
    dry_run: bool
    error: Optional[str] = None


# Authentication dependency
async def get_current_user(current_user: User = Depends(get_current_user_from_jwt)):
    """Get current authenticated user from enhanced JWT token"""
    return current_user
    
    logger.debug(f"User authenticated: {user.email}, role: {user.role.name if user.role else 'None'}")
    return user


# Notification service dependency
def get_notification_service_with_websocket(
    db: Session = Depends(get_db),
    websocket_manager: WebSocketManager = Depends(get_websocket_manager)
) -> NotificationService:
    """Get notification service with WebSocket manager"""
    return get_notification_service(db, websocket_manager)


@router.get("/notifications", response_model=NotificationListResponse)
async def get_notifications(
    limit: int = Query(50, ge=1, le=100, description="Maximum number of notifications to return"),
    unread_only: bool = Query(False, description="If true, only return unread notifications"),
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service_with_websocket)
):
    """
    Get user's notifications.
    
    Returns a list of notifications for the authenticated user, with options to:
    - Limit the number of results (default: 50, max: 100)
    - Filter to only unread notifications
    
    Requirements: 5.1, 5.3, 5.5
    """
    try:
        # Get notifications using the service
        notifications = notification_service.get_user_notifications(
            user_id=current_user.id,
            limit=limit,
            unread_only=unread_only
        )
        
        # Get unread count
        unread_count = notification_service.get_unread_count(current_user.id)
        
        # Convert to response format
        notification_responses = []
        for notification in notifications:
            notification_responses.append(NotificationResponse(
                id=notification.id,
                title=notification.title,
                message=notification.message,
                type=notification.type,
                read=notification.read,
                read_at=notification.read_at.isoformat() if notification.read_at else None,
                action_type=notification.action_type,
                action_target=notification.action_target,
                action_params=notification.action_params,
                created_at=notification.created_at.isoformat() if notification.created_at else None,
                expires_at=notification.expires_at.isoformat() if notification.expires_at else None
            ))
        
        logger.debug(f"Retrieved {len(notifications)} notifications for user {current_user.id}")
        
        return NotificationListResponse(
            notifications=notification_responses,
            total=len(notifications),
            unread_count=unread_count
        )
        
    except Exception as e:
        logger.error(f"Error retrieving notifications for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve notifications"
        )


@router.post("/notifications/{notification_id}/read", response_model=MarkReadResponse)
async def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service_with_websocket)
):
    """
    Mark a specific notification as read.
    
    The notification must belong to the authenticated user. If the notification
    is already read, this operation is idempotent and will succeed.
    
    Requirements: 5.1
    """
    try:
        # Mark notification as read
        success = notification_service.mark_as_read(notification_id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found or does not belong to you"
            )
        
        logger.debug(f"Marked notification {notification_id} as read for user {current_user.id}")
        
        return MarkReadResponse(
            success=True,
            message="Notification marked as read",
            notification_id=notification_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification {notification_id} as read for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark notification as read"
        )


@router.post("/notifications/read-all", response_model=MarkAllReadResponse)
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service_with_websocket)
):
    """
    Mark all notifications as read for the authenticated user.
    
    This operation marks all unread notifications for the user as read.
    Returns the count of notifications that were marked as read.
    
    Requirements: 5.2
    """
    try:
        # Mark all notifications as read
        marked_count = notification_service.mark_all_as_read(current_user.id)
        
        logger.debug(f"Marked {marked_count} notifications as read for user {current_user.id}")
        
        return MarkAllReadResponse(
            success=True,
            message=f"Marked {marked_count} notifications as read",
            marked_count=marked_count
        )
        
    except Exception as e:
        logger.error(f"Error marking all notifications as read for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark notifications as read"
        )


@router.post("/notifications", response_model=NotificationResponse)
async def create_test_notification(
    request: CreateNotificationRequest,
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service_with_websocket)
):
    """
    Create a test notification (for testing purposes).
    
    This endpoint allows creating notifications for testing the real-time
    notification system. In production, notifications are typically created
    by system events rather than direct API calls.
    """
    try:
        # Determine target user (default to current user if not specified)
        target_user_id = request.user_id if request.user_id else current_user.id
        
        # Validate notification type
        valid_types = ["info", "success", "warning", "danger"]
        if request.type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid notification type. Must be one of: {valid_types}"
            )
        
        # Create the notification
        notification = notification_service.notify_user(
            user_id=target_user_id,
            title=request.title,
            message=request.message,
            notification_type=request.type,
            created_by=current_user.id
        )
        
        logger.debug(f"Test notification created: {notification.id} for user {target_user_id}")
        
        # Convert to response format
        return NotificationResponse(
            id=notification.id,
            title=notification.title,
            message=notification.message,
            type=notification.type,
            read=notification.read,
            read_at=notification.read_at.isoformat() if notification.read_at else None,
            action_type=notification.action_type,
            action_target=notification.action_target,
            action_params=notification.action_params,
            created_at=notification.created_at.isoformat() if notification.created_at else None,
            expires_at=notification.expires_at.isoformat() if notification.expires_at else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating test notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create notification"
        )
        
    except Exception as e:
        logger.error(f"Error marking all notifications as read for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark all notifications as read"
        )


# WebSocket endpoints moved to websocket_api.py to avoid collisions


@router.get("/notifications/stats")
async def get_notification_stats(
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service_with_websocket)
):
    """
    Get notification statistics for the authenticated user.
    
    Returns:
    - unread_count: Number of unread notifications
    - total_count: Total number of notifications (recent)
    
    This endpoint is useful for updating UI badges and counters.
    """
    try:
        unread_count = notification_service.get_unread_count(current_user.id)
        
        # Get total recent notifications (last 100)
        recent_notifications = notification_service.get_user_notifications(
            user_id=current_user.id,
            limit=100,
            unread_only=False
        )
        total_count = len(recent_notifications)
        
        return {
            "unread_count": unread_count,
            "total_count": total_count,
            "user_id": current_user.id
        }
        
    except Exception as e:
        logger.error(f"Error getting notification stats for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get notification statistics"
        )


# WebSocket stats moved to websocket_api.py


@router.get("/cleanup/stats", response_model=CleanupStatsResponse)
async def get_cleanup_stats(
    current_user: User = Depends(get_current_user)
):
    """
    Get notification cleanup statistics.
    
    Shows how many notifications would be cleaned up by the cleanup service
    and the current configuration. Useful for monitoring and planning.
    
    Requirements: 8.4
    """
    try:
        # Check if user has admin role for cleanup operations
        if not current_user.role or current_user.role.name != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin role required for cleanup operations"
            )
        
        cleanup_service = get_cleanup_service()
        stats = cleanup_service.get_cleanup_stats()
        
        return CleanupStatsResponse(
            counts=stats["counts"],
            cutoff_dates=stats["cutoff_dates"],
            config=stats["config"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting cleanup stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get cleanup statistics"
        )


@router.post("/cleanup/run", response_model=CleanupResultResponse)
async def run_cleanup_manually(
    dry_run: bool = Query(False, description="If true, only simulate cleanup without deleting"),
    current_user: User = Depends(get_current_user)
):
    """
    Manually trigger notification cleanup.
    
    This endpoint allows administrators to manually run the notification cleanup
    process. Useful for testing or immediate cleanup needs.
    
    Args:
        dry_run: If true, only simulate the cleanup without actually deleting notifications
    
    Requirements: 8.4
    """
    try:
        # Check if user has admin role for cleanup operations
        if not current_user.role or current_user.role.name != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin role required for cleanup operations"
            )
        
        # Get cleanup service and temporarily set dry_run mode if requested
        cleanup_service = get_cleanup_service()
        original_dry_run = cleanup_service.config.dry_run
        
        if dry_run:
            cleanup_service.config.dry_run = True
        
        try:
            # Run cleanup
            result = cleanup_service.run_cleanup()
            
            logger.info(f"Manual cleanup triggered by user {current_user.id}, "
                       f"dry_run={dry_run}, result={result}")
            
            return CleanupResultResponse(
                success=result["success"],
                total_deleted=result["total_deleted"],
                categories=result["categories"],
                execution_time=result["execution_time"],
                vacuum_run=result["vacuum_run"],
                dry_run=result["dry_run"],
                error=result.get("error")
            )
            
        finally:
            # Restore original dry_run setting
            cleanup_service.config.dry_run = original_dry_run
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running manual cleanup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to run cleanup process"
        )


@router.get("/cleanup/scheduler/status")
async def get_cleanup_scheduler_status(
    current_user: User = Depends(get_current_user)
):
    """
    Get status of the background cleanup scheduler.
    
    Shows information about the scheduled cleanup task including:
    - Whether it's enabled and running
    - Last run time and next scheduled run
    - Run count and error statistics
    
    Requirements: 8.4
    """
    try:
        # Check if user has admin role for cleanup operations
        if not current_user.role or current_user.role.name != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin role required for cleanup operations"
            )
        
        scheduler = get_scheduler()
        
        # Get overall scheduler stats
        scheduler_stats = scheduler.get_task_stats()
        
        # Get specific cleanup task status
        cleanup_task_status = scheduler.get_task_status("notification_cleanup")
        
        return {
            "scheduler_running": scheduler_stats["running"],
            "total_tasks": scheduler_stats["total_tasks"],
            "enabled_tasks": scheduler_stats["enabled_tasks"],
            "cleanup_task": cleanup_task_status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting cleanup scheduler status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get scheduler status"
        )


@router.post("/cleanup/scheduler/enable")
async def enable_cleanup_scheduler(
    current_user: User = Depends(get_current_user)
):
    """
    Enable the background cleanup scheduler task.
    
    Requirements: 8.4
    """
    try:
        # Check if user has admin role for cleanup operations
        if not current_user.role or current_user.role.name != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin role required for cleanup operations"
            )
        
        scheduler = get_scheduler()
        success = scheduler.enable_task("notification_cleanup")
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cleanup task not found"
            )
        
        logger.info(f"Cleanup scheduler enabled by user {current_user.id}")
        
        return {
            "success": True,
            "message": "Cleanup scheduler enabled"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enabling cleanup scheduler: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to enable cleanup scheduler"
        )


@router.post("/cleanup/scheduler/disable")
async def disable_cleanup_scheduler(
    current_user: User = Depends(get_current_user)
):
    """
    Disable the background cleanup scheduler task.
    
    Requirements: 8.4
    """
    try:
        # Check if user has admin role for cleanup operations
        if not current_user.role or current_user.role.name != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin role required for cleanup operations"
            )
        
        scheduler = get_scheduler()
        success = scheduler.disable_task("notification_cleanup")
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cleanup task not found"
            )
        
        logger.info(f"Cleanup scheduler disabled by user {current_user.id}")
        
        return {
            "success": True,
            "message": "Cleanup scheduler disabled"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disabling cleanup scheduler: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disable cleanup scheduler"
        )