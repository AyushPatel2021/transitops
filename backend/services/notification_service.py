from typing import List, Optional, Union, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from backend.core.base_model import Environment
from backend.core.websocket_manager import get_websocket_manager
from backend.models.notification import Notification
from backend.models.user import User
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Core notification service for creating, managing, and delivering notifications.
    Supports both user ID list targeting and recordset targeting.
    """
    
    def __init__(self, db: Session, websocket_manager=None):
        """
        Initialize notification service.
        
        Args:
            db: Database session
            websocket_manager: WebSocket manager for real-time delivery (optional)
        """
        self.db = db
        self.env = Environment(db)
        self.websocket_manager = websocket_manager
    
    def notify_user(
        self, 
        user_id: int, 
        title: str, 
        message: str,
        notification_type: str = "info", 
        action: Optional[Dict[str, Any]] = None,
        created_by: Optional[int] = None, 
        expires_in_hours: Optional[int] = None
    ) -> Notification:
        """
        Send notification to a specific user.
        
        Args:
            user_id: Target user ID
            title: Notification title
            message: Notification message content
            notification_type: Type of notification (info, success, warning, danger)
            action: Action configuration dict with type, target, and params
            created_by: ID of user creating the notification
            expires_in_hours: Hours until notification expires (None for no expiration)
            
        Returns:
            Created Notification instance
            
        Raises:
            ValueError: If user_id is invalid or notification data is malformed
        """
        # Validate user exists
        user = self.env['user'].browse(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        # Validate notification type
        valid_types = ["info", "success", "warning", "danger"]
        if notification_type not in valid_types:
            raise ValueError(f"Invalid notification type. Must be one of: {valid_types}")
        
        # Calculate expiration time
        expires_at = None
        if expires_in_hours is not None:
            expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
        
        # Parse action configuration
        action_type = None
        action_target = None
        action_params = None
        
        if action:
            action_type = action.get("type")
            action_target = action.get("target")
            action_params = action.get("params")
            
            # Validate action type
            valid_action_types = ["navigate", "modal", "function"]
            if action_type and action_type not in valid_action_types:
                raise ValueError(f"Invalid action type. Must be one of: {valid_action_types}")
        
        try:
            # Create notification record
            notification_data = {
                'title': title,
                'message': message,
                'type': notification_type,
                'user_id': user_id,
                'action_type': action_type,
                'action_target': action_target,
                'action_params': action_params,
                'expires_at': expires_at
            }
            
            # Only add created_by if it's provided and valid
            if created_by:
                # Verify the user exists before adding
                creator = self.env['user'].browse(created_by)
                if creator and creator.id:
                    notification_data['created_by'] = created_by
                else:
                    logger.warning(f"⚠️ created_by user {created_by} not found, creating notification without creator")
            
            notification = self.env['notification'].create(notification_data)
            
            # notification is now a Recordset, we need the record for WebSocket
            record = notification[0]
            
            # Send real-time notification if WebSocket manager available
            if self.websocket_manager:
                try:
                    import asyncio
                    
                    # Convert notification to dictionary format for WebSocket
                    websocket_message = record.to_websocket_message()
                    notification_dict = websocket_message['data']['notification']
                    
                    # The frontend expects server_id
                    if 'server_id' not in notification_dict:
                        notification_dict['server_id'] = str(record.id)
                    
                    # Get the actual user ID (Many2one field returns object, we need the ID)
                    target_user_id = record.user_id.id if hasattr(record.user_id, 'id') else record.user_id
                    
                    # Send WebSocket message using create_task (fire and forget)
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            task = loop.create_task(
                                self.websocket_manager.broadcast_notification(notification_dict)
                            )
                        else:
                            loop.run_until_complete(
                                self.websocket_manager.broadcast_notification(notification_dict)
                            )
                    except RuntimeError as re:
                        asyncio.run(
                            self.websocket_manager.broadcast_notification(notification_dict)
                        )
                        
                except Exception as e:
                    logger.warning(f"Failed to send real-time notification: {e}")
            
            logger.info(f"Created notification {record.id} for user {user_id}")
            return record
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create notification for user {user_id}: {e}")
            raise
    
    def notify_users(
        self, 
        user_ids: List[int], 
        title: str, 
        message: str,
        notification_type: str = "info", 
        action: Optional[Dict[str, Any]] = None,
        created_by: Optional[int] = None, 
        expires_in_hours: Optional[int] = None
    ) -> List[Notification]:
        """
        Send notification to multiple users by user IDs.
        
        Args:
            user_ids: List of target user IDs
            title: Notification title
            message: Notification message content
            notification_type: Type of notification (info, success, warning, danger)
            action: Action configuration dict with type, target, and params
            created_by: ID of user creating the notification
            expires_in_hours: Hours until notification expires (None for no expiration)
            
        Returns:
            List of created Notification instances
            
        Raises:
            ValueError: If user_ids is empty or contains invalid IDs
        """
        if not user_ids:
            raise ValueError("user_ids cannot be empty")
        
        # Validate all users exist
        existing_users = self.env['user'].browse(user_ids)
        existing_user_ids = set(existing_users.mapped('id'))
        invalid_ids = set(user_ids) - existing_user_ids
        
        if invalid_ids:
            raise ValueError(f"Invalid user IDs: {invalid_ids}")
        
        notifications = []
        
        try:
            # Create notifications for each user
            for user_id in user_ids:
                notification = self.notify_user(
                    user_id=user_id,
                    title=title,
                    message=message,
                    notification_type=notification_type,
                    action=action,
                    created_by=created_by,
                    expires_in_hours=expires_in_hours
                )
                notifications.append(notification)
            
            logger.info(f"Created {len(notifications)} notifications for users {user_ids}")
            return notifications
            
        except Exception as e:
            logger.error(f"Failed to create notifications for users {user_ids}: {e}")
            raise
    
    def notify_recordset(
        self, 
        users, 
        title: str, 
        message: str,
        notification_type: str = "info", 
        action: Optional[Dict[str, Any]] = None,
        created_by: Optional[int] = None, 
        expires_in_hours: Optional[int] = None
    ) -> List[Notification]:
        """
        Send notification to users from a recordset.
        
        Args:
            users: User recordset or list of User objects
            title: Notification title
            message: Notification message content
            notification_type: Type of notification (info, success, warning, danger)
            action: Action configuration dict with type, target, and params
            created_by: ID of user creating the notification
            expires_in_hours: Hours until notification expires (None for no expiration)
            
        Returns:
            List of created Notification instances
            
        Raises:
            ValueError: If users is empty or invalid
        """
        # Extract user IDs from recordset or list of User objects
        user_ids = []
        
        try:
            # Handle different types of user collections
            if hasattr(users, '_records'):
                # Recordset object
                user_ids = [user.id for user in users._records if hasattr(user, 'id')]
            elif hasattr(users, '__iter__'):
                # List or other iterable
                for user in users:
                    if hasattr(user, 'id'):
                        user_ids.append(user.id)
                    elif isinstance(user, int):
                        user_ids.append(user)
                    else:
                        raise ValueError(f"Invalid user object: {user}")
            else:
                raise ValueError("users must be a recordset or iterable of User objects")
            
            if not user_ids:
                raise ValueError("No valid user IDs found in recordset")
            
            # Use notify_users to handle the actual notification creation
            return self.notify_users(
                user_ids=user_ids,
                title=title,
                message=message,
                notification_type=notification_type,
                action=action,
                created_by=created_by,
                expires_in_hours=expires_in_hours
            )
            
        except Exception as e:
            logger.error(f"Failed to create notifications for recordset: {e}")
            raise
    
    def get_user_notifications(
        self, 
        user_id: int, 
        limit: int = 50, 
        unread_only: bool = False
    ) -> List[Notification]:
        """
        Get notifications for a user.
        
        Args:
            user_id: User ID to get notifications for
            limit: Maximum number of notifications to return
            unread_only: If True, only return unread notifications
            
        Returns:
            List of Notification instances
        """
        domain = [('user_id', '=', user_id)]
        if unread_only:
            domain.append(('read', '=', False))
        
        return self.env['notification'].search(domain, limit=limit, order='created_at desc')
    
    def mark_as_read(self, notification_id: int, user_id: int) -> bool:
        """
        Mark notification as read.
        
        Args:
            notification_id: ID of notification to mark as read
            user_id: ID of user marking the notification (for security)
            
        Returns:
            True if successful, False if notification not found or not owned by user
        """
        notification = self.env['notification'].search([
            ('id', '=', notification_id),
            ('user_id', '=', user_id)
        ], limit=1)
        
        if not notification:
            return False
        
        if not notification.read:
            notification.mark_as_read()
            
            # Commit the transaction to ensure changes are persisted
            try:
                self.db.commit()
            except Exception as e:
                logger.error(f"Failed to commit mark as read for notification {notification_id}: {e}")
                self.db.rollback()
                raise
            
            # Send real-time update if WebSocket manager available
            if self.websocket_manager:
                try:
                    import asyncio
                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    
                    # Send read status update
                    message = {
                        "type": "notification_read",
                        "data": {
                            "notification_id": str(notification_id),
                            "user_id": user_id
                        }
                    }
                    loop.create_task(
                        self.websocket_manager.send_to_user(user_id, message)
                    )
                except Exception as e:
                    logger.warning(f"Failed to send real-time read update: {e}")
        
        return True
    
    def mark_all_as_read(self, user_id: int) -> int:
        """
        Mark all notifications as read for a user.
        
        Args:
            user_id: User ID to mark all notifications as read for
            
        Returns:
            Number of notifications marked as read
        """
        # Use direct SQLAlchemy query for reliable results
        from backend.models.notification import Notification as NotificationModel
        
        try:
            # Direct database query
            unread_records = self.db.query(NotificationModel).filter(
                NotificationModel.user_id == user_id,
                NotificationModel.read == False
            ).all()
            
            updated_count = len(unread_records)
            
            if updated_count > 0:
                notification_ids = [n.id for n in unread_records]
                
                # Update directly using SQLAlchemy
                self.db.query(NotificationModel).filter(
                    NotificationModel.id.in_(notification_ids)
                ).update(
                    {
                        'read': True,
                        'read_at': datetime.utcnow()
                    },
                    synchronize_session=False
                )
                
                # Commit the changes
                self.db.commit()
                
                # Send real-time update if WebSocket manager available
                if self.websocket_manager:
                    try:
                        import asyncio
                        try:
                            loop = asyncio.get_event_loop()
                        except RuntimeError:
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                        
                        # Send bulk read status update
                        message = {
                            "type": "notifications_read_all",
                            "data": {
                                "user_id": user_id,
                                "count": updated_count
                            }
                        }
                        loop.create_task(
                            self.websocket_manager.send_to_user(user_id, message)
                        )
                    except Exception as e:
                        logger.warning(f"Failed to send real-time bulk read update: {e}")
                
        except Exception as e:
            logger.error(f"Error marking all as read for user {user_id}: {e}")
            self.db.rollback()
            raise
        
        logger.info(f"Marked {updated_count} notifications as read for user {user_id}")
        return updated_count
    
    def cleanup_expired_notifications(self) -> int:
        """
        Remove expired notifications.
        
        Returns:
            Number of notifications removed
        """
        expired = self.env['notification'].search([
            ('expires_at', '<', datetime.utcnow())
        ])
        expired_count = len(expired)
        
        if expired_count > 0:
            expired.unlink()
            logger.info(f"Cleaned up {expired_count} expired notifications")
        
        return expired_count
    
    def get_unread_count(self, user_id: int) -> int:
        """
        Get count of unread notifications for a user.
        
        Args:
            user_id: User ID to get unread count for
            
        Returns:
            Number of unread notifications
        """
        return len(self.env['notification'].search([
            ('user_id', '=', user_id),
            ('read', '=', False)
        ]))


# Dependency injection helper for FastAPI
def get_notification_service(db: Session, websocket_manager=None) -> NotificationService:
    """
    Create NotificationService instance with dependencies.
    
    Args:
        db: Database session
        websocket_manager: WebSocket manager (optional)
        
    Returns:
        NotificationService instance
    """
    if websocket_manager is None:
        try:
            websocket_manager = get_websocket_manager()
        except (ImportError, AttributeError):
            pass

    return NotificationService(db, websocket_manager)
