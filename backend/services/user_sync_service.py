"""
User Synchronization Service

This service handles real-time user data synchronization across multiple
sessions and devices using WebSocket connections.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from backend.core.websocket_manager import WebSocketManager

logger = logging.getLogger(__name__)


class UserSyncService:
    """
    Service for managing real-time user data synchronization.
    
    This service provides methods to broadcast user data changes,
    role updates, and other user-related events to all active
    WebSocket connections for a specific user.
    """
    
    def __init__(self, websocket_manager: WebSocketManager):
        self.websocket_manager = websocket_manager
    
    async def broadcast_user_data_update(
        self, 
        user_id: int, 
        updates: Dict[str, Any],
        exclude_connection: Optional[Any] = None
    ) -> int:
        """
        Broadcast user data updates to all connections for a user.
        
        Args:
            user_id: ID of the user whose data was updated
            updates: Dictionary of updated fields
            exclude_connection: WebSocket connection to exclude from broadcast
            
        Returns:
            int: Number of connections the update was sent to
        """
        message = {
            "type": "user_data_updated",
            "data": {
                "user_id": user_id,
                "updates": updates
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"📡 Broadcasting user data update for user {user_id}: {list(updates.keys())}")
        
        sent_count = await self.websocket_manager.send_to_user(user_id, message)
        logger.info(f"📊 User data update sent to {sent_count} connections for user {user_id}")
        
        return sent_count
    
    async def broadcast_user_preferences_update(
        self, 
        user_id: int, 
        preferences: Dict[str, Any],
        exclude_connection: Optional[Any] = None
    ) -> int:
        """
        Broadcast user preference updates to all connections for a user.
        
        Args:
            user_id: ID of the user whose preferences were updated
            preferences: Dictionary of updated preferences
            exclude_connection: WebSocket connection to exclude from broadcast
            
        Returns:
            int: Number of connections the update was sent to
        """
        message = {
            "type": "user_preferences_updated",
            "data": {
                "user_id": user_id,
                "preferences": preferences
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"📡 Broadcasting user preferences update for user {user_id}: {list(preferences.keys())}")
        
        sent_count = await self.websocket_manager.send_to_user(user_id, message)
        logger.info(f"📊 User preferences update sent to {sent_count} connections for user {user_id}")
        
        return sent_count
    
    async def broadcast_user_role_change(
        self, 
        user_id: int, 
        new_role: str,
        new_permissions: List[str],
        exclude_connection: Optional[Any] = None
    ) -> int:
        """
        Broadcast user role/permission changes to all connections for a user.
        
        This is a critical update that will trigger token refresh on the client.
        
        Args:
            user_id: ID of the user whose role was changed
            new_role: New role name
            new_permissions: New permissions list
            exclude_connection: WebSocket connection to exclude from broadcast
            
        Returns:
            int: Number of connections the update was sent to
        """
        message = {
            "type": "user_role_changed",
            "data": {
                "user_id": user_id,
                "new_role": new_role,
                "new_permissions": new_permissions,
                "requires_token_refresh": True
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"📡 Broadcasting user role change for user {user_id}: {new_role}")
        
        sent_count = await self.websocket_manager.send_to_user(user_id, message)
        logger.info(f"📊 User role change sent to {sent_count} connections for user {user_id}")
        
        return sent_count
    
    async def broadcast_user_deactivation(
        self, 
        user_id: int,
        reason: str = "Account deactivated",
        exclude_connection: Optional[Any] = None
    ) -> int:
        """
        Broadcast user account deactivation to all connections for a user.
        
        This will trigger immediate logout on all client sessions.
        
        Args:
            user_id: ID of the user whose account was deactivated
            reason: Reason for deactivation
            exclude_connection: WebSocket connection to exclude from broadcast
            
        Returns:
            int: Number of connections the update was sent to
        """
        message = {
            "type": "user_deactivated",
            "data": {
                "user_id": user_id,
                "reason": reason,
                "force_logout": True
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"📡 Broadcasting user deactivation for user {user_id}: {reason}")
        
        sent_count = await self.websocket_manager.send_to_user(user_id, message)
        logger.info(f"📊 User deactivation sent to {sent_count} connections for user {user_id}")
        
        return sent_count
    
    async def broadcast_force_logout(
        self, 
        user_id: int,
        reason: str = "Session terminated",
        exclude_connection: Optional[Any] = None
    ) -> int:
        """
        Broadcast force logout to all connections for a user.
        
        This will trigger immediate logout on all client sessions.
        
        Args:
            user_id: ID of the user to force logout
            reason: Reason for force logout
            exclude_connection: WebSocket connection to exclude from broadcast
            
        Returns:
            int: Number of connections the update was sent to
        """
        message = {
            "type": "force_logout",
            "data": {
                "user_id": user_id,
                "reason": reason,
                "timestamp": datetime.utcnow().isoformat()
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"📡 Broadcasting force logout for user {user_id}: {reason}")
        
        sent_count = await self.websocket_manager.send_to_user(user_id, message)
        logger.info(f"📊 Force logout sent to {sent_count} connections for user {user_id}")
        
        return sent_count
    
    async def broadcast_to_multiple_users(
        self, 
        user_ids: List[int], 
        message_type: str,
        data: Dict[str, Any]
    ) -> int:
        """
        Broadcast a message to multiple users.
        
        Args:
            user_ids: List of user IDs to send to
            message_type: Type of message
            data: Message data
            
        Returns:
            int: Total number of connections the message was sent to
        """
        message = {
            "type": message_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"📡 Broadcasting {message_type} to {len(user_ids)} users")
        
        total_sent = await self.websocket_manager.send_to_users(user_ids, message)
        logger.info(f"📊 Message sent to {total_sent} total connections across {len(user_ids)} users")
        
        return total_sent
    
    def get_active_user_connections(self, user_id: int) -> int:
        """
        Get the number of active connections for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            int: Number of active connections
        """
        stats = self.websocket_manager.get_connection_stats()
        return stats.get("user_connection_counts", {}).get(user_id, 0)
    
    def get_all_active_users(self) -> List[int]:
        """
        Get list of all users with active connections.
        
        Returns:
            List[int]: List of user IDs with active connections
        """
        stats = self.websocket_manager.get_connection_stats()
        return list(stats.get("user_connection_counts", {}).keys())


def get_user_sync_service(websocket_manager: WebSocketManager) -> UserSyncService:
    """
    Dependency function to get the user synchronization service.
    
    Args:
        websocket_manager: WebSocket manager instance
        
    Returns:
        UserSyncService: User synchronization service instance
    """
    return UserSyncService(websocket_manager)