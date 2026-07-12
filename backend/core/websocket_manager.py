"""
WebSocket Manager for Real-time Notifications

This module provides WebSocket connection management for the notification system,
including user authentication, connection tracking, message broadcasting, and
heartbeat functionality.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ConnectionInfo:
    """Information about a WebSocket connection"""
    
    def __init__(self, websocket: WebSocket, user_id: int, user_email: str):
        self.websocket = websocket
        self.user_id = user_id
        self.user_email = user_email
        self.connected_at = datetime.utcnow()
        self.last_heartbeat = datetime.utcnow()
        self.is_alive = True


class WebSocketManager:
    """
    Manages WebSocket connections for real-time notifications.
    
    Features:
    - User authentication and connection tracking
    - Message broadcasting to specific users or all users
    - Heartbeat functionality for connection health monitoring
    - Automatic cleanup of dead connections
    """
    
    def __init__(self):
        # Map of user_id -> list of ConnectionInfo objects
        self.active_connections: Dict[int, List[ConnectionInfo]] = {}
        # Map of WebSocket -> ConnectionInfo for quick lookup
        self.connection_metadata: Dict[WebSocket, ConnectionInfo] = {}
        # Set of all active WebSocket connections
        self.all_connections: Set[WebSocket] = set()
        
        # Heartbeat configuration
        self.heartbeat_interval = 30  # seconds
        self.heartbeat_timeout = 60   # seconds
        self._heartbeat_task: Optional[asyncio.Task] = None
        
        logger.info("WebSocketManager initialized")
    
    async def connect(self, websocket: WebSocket, user_id: int, user_email: str) -> bool:
        """
        Accept WebSocket connection and register user.
        
        Args:
            websocket: The WebSocket connection
            user_id: ID of the authenticated user
            user_email: Email of the authenticated user
            
        Returns:
            bool: True if connection was successful
        """
        try:
            await websocket.accept()
            logger.info(f"🔌 WebSocket connection accepted for user {user_id} ({user_email})")
            
            # Create connection info
            conn_info = ConnectionInfo(websocket, user_id, user_email)
            
            # Add to user connections
            if user_id not in self.active_connections:
                self.active_connections[user_id] = []
            self.active_connections[user_id].append(conn_info)
            
            # Add to metadata maps
            self.connection_metadata[websocket] = conn_info
            self.all_connections.add(websocket)
            
            # Start heartbeat task if this is the first connection
            if len(self.all_connections) == 1 and self._heartbeat_task is None:
                self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
                logger.info("💓 Started heartbeat loop")
            
            logger.info(f"✅ WebSocket connected: user_id={user_id}, email={user_email}, "
                       f"user_connections={len(self.active_connections[user_id])}, "
                       f"total_connections={len(self.all_connections)}")
            
            # Send welcome message
            await self._send_to_connection(websocket, {
                "type": "connection_established",
                "data": {
                    "user_id": user_id,
                    "connected_at": conn_info.connected_at.isoformat(),
                    "message": "WebSocket connection established"
                }
            })
            
            logger.info(f"📨 Welcome message sent to user {user_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect WebSocket for user {user_id}: {e}")
            return False
    
    def disconnect(self, websocket: WebSocket) -> None:
        """
        Remove WebSocket connection and clean up.
        
        Args:
            websocket: The WebSocket connection to remove
        """
        if websocket not in self.connection_metadata:
            return
        
        conn_info = self.connection_metadata[websocket]
        user_id = conn_info.user_id
        
        # Remove from user connections
        if user_id in self.active_connections:
            self.active_connections[user_id] = [
                conn for conn in self.active_connections[user_id] 
                if conn.websocket != websocket
            ]
            # Remove user entry if no connections left
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        
        # Remove from metadata maps
        del self.connection_metadata[websocket]
        self.all_connections.discard(websocket)
        
        # Stop heartbeat task if no connections left
        if not self.all_connections and self._heartbeat_task:
            self._heartbeat_task.cancel()
            self._heartbeat_task = None
        
        logger.info(f"WebSocket disconnected: user_id={user_id}, email={conn_info.user_email}, "
                   f"remaining_connections={len(self.all_connections)}")
    
    async def send_to_user(self, user_id: int, message: dict) -> int:
        """
        Send message to all connections for a specific user.
        
        Args:
            user_id: ID of the target user
            message: Message dictionary to send
            
        Returns:
            int: Number of connections the message was sent to
        """
        if user_id not in self.active_connections:
            logger.debug(f"No active connections for user {user_id}")
            return 0
        
        connections = self.active_connections[user_id].copy()
        sent_count = 0
        failed_connections = []
        
        for conn_info in connections:
            try:
                await self._send_to_connection(conn_info.websocket, message)
                sent_count += 1
            except Exception as e:
                logger.warning(f"Failed to send message to user {user_id}: {e}")
                failed_connections.append(conn_info.websocket)
        
        # Clean up failed connections
        for websocket in failed_connections:
            self.disconnect(websocket)
        
        logger.debug(f"Sent message to {sent_count} connections for user {user_id}")
        return sent_count
    
    async def send_to_users(self, user_ids: List[int], message: dict) -> int:
        """
        Send message to multiple users.
        
        Args:
            user_ids: List of user IDs to send to
            message: Message dictionary to send
            
        Returns:
            int: Total number of connections the message was sent to
        """
        total_sent = 0
        for user_id in user_ids:
            sent_count = await self.send_to_user(user_id, message)
            total_sent += sent_count
        
        logger.debug(f"Sent message to {total_sent} total connections across {len(user_ids)} users")
        return total_sent
    
    async def broadcast_to_all(self, message: dict) -> int:
        """
        Broadcast message to all connected users.
        
        Args:
            message: Message dictionary to send
            
        Returns:
            int: Number of connections the message was sent to
        """
        connections = list(self.all_connections)
        sent_count = 0
        failed_connections = []
        
        for websocket in connections:
            try:
                await self._send_to_connection(websocket, message)
                sent_count += 1
            except Exception as e:
                conn_info = self.connection_metadata.get(websocket)
                user_info = f"user_id={conn_info.user_id}" if conn_info else "unknown"
                logger.warning(f"Failed to broadcast to {user_info}: {e}")
                failed_connections.append(websocket)
        
        # Clean up failed connections
        for websocket in failed_connections:
            self.disconnect(websocket)
        
        logger.debug(f"Broadcast message to {sent_count} connections")
        return sent_count
    
    async def broadcast_notification(self, notification_data: dict) -> int:
        """
        Broadcast a notification to the target user.
        
        Args:
            notification_data: Notification data including user_id
            
        Returns:
            int: Number of connections the notification was sent to
        """
        user_id = notification_data.get("user_id")
        if not user_id:
            logger.error("Cannot broadcast notification without user_id")
            return 0
        
        message = {
            "type": "notification",
            "data": {
                "action": "new",
                "notification": notification_data
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        sent_count = await self.send_to_user(user_id, message)
        
        return sent_count
    
    async def handle_client_message(self, websocket: WebSocket, message_data: dict) -> None:
        """
        Handle incoming message from client.
        
        Args:
            websocket: The WebSocket connection
            message_data: Parsed message data from client
        """
        if websocket not in self.connection_metadata:
            logger.warning("Received message from unregistered WebSocket")
            return
        
        conn_info = self.connection_metadata[websocket]
        message_type = message_data.get("type")
        
        if message_type == "heartbeat":
            # Update last heartbeat time
            conn_info.last_heartbeat = datetime.utcnow()
            
            # Send heartbeat response
            await self._send_to_connection(websocket, {
                "type": "heartbeat_response",
                "data": {
                    "timestamp": datetime.utcnow().isoformat()
                }
            })
            
        elif message_type == "mark_read":
            # Handle mark as read request
            notification_id = message_data.get("data", {}).get("notification_id")
            if notification_id:
                logger.debug(f"User {conn_info.user_id} marked notification {notification_id} as read")
                # Note: The actual marking as read will be handled by the notification service
                # This is just for logging/tracking purposes
        
        elif message_type == "notifications_read_all":
            # Handle mark all notifications as read request
            logger.debug(f"User {conn_info.user_id} marked all notifications as read")
            # Note: The actual marking as read will be handled by the notification service
            # This is just for logging/tracking purposes
        
        elif message_type == "mark_all_read":
            # Alternative message type for mark all as read
            logger.debug(f"User {conn_info.user_id} marked all notifications as read (mark_all_read)")
            # Note: The actual marking as read will be handled by the notification service
            # This is just for logging/tracking purposes
        
        elif message_type == "ping":
            # Handle ping messages (alternative to heartbeat)
            conn_info.last_heartbeat = datetime.utcnow()
            await self._send_to_connection(websocket, {
                "type": "pong",
                "data": {
                    "timestamp": datetime.utcnow().isoformat()
                }
            })
        
        else:
            logger.debug(f"Received unknown message type '{message_type}' from user {conn_info.user_id}")
    
    def get_connection_stats(self) -> dict:
        """
        Get statistics about current connections.
        
        Returns:
            dict: Connection statistics
        """
        total_connections = len(self.all_connections)
        unique_users = len(self.active_connections)
        
        user_connection_counts = {
            user_id: len(connections) 
            for user_id, connections in self.active_connections.items()
        }
        
        return {
            "total_connections": total_connections,
            "unique_users": unique_users,
            "user_connection_counts": user_connection_counts,
            "heartbeat_interval": self.heartbeat_interval,
            "heartbeat_timeout": self.heartbeat_timeout
        }
    
    async def _send_to_connection(self, websocket: WebSocket, message: dict) -> None:
        """
        Send message to a specific WebSocket connection.
        
        Args:
            websocket: The WebSocket connection
            message: Message dictionary to send
        """
        try:
            message_json = json.dumps(message)
            await websocket.send_text(message_json)
        except Exception as e:
            # Connection is likely closed, will be cleaned up by caller
            raise e
    
    async def _heartbeat_loop(self) -> None:
        """
        Background task that sends periodic heartbeats and cleans up dead connections.
        """
        logger.info("Starting WebSocket heartbeat loop")
        
        try:
            while True:
                await asyncio.sleep(self.heartbeat_interval)
                
                if not self.all_connections:
                    logger.debug("No active connections, stopping heartbeat loop")
                    break
                
                await self._send_heartbeats()
                await self._cleanup_dead_connections()
                
        except asyncio.CancelledError:
            logger.info("Heartbeat loop cancelled")
        except Exception as e:
            logger.error(f"Error in heartbeat loop: {e}")
        finally:
            self._heartbeat_task = None
    
    async def _send_heartbeats(self) -> None:
        """Send heartbeat messages to all connections."""
        if not self.all_connections:
            return
        
        heartbeat_message = {
            "type": "heartbeat",
            "data": {
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        connections = list(self.all_connections)
        failed_connections = []
        
        for websocket in connections:
            try:
                await self._send_to_connection(websocket, heartbeat_message)
            except Exception:
                failed_connections.append(websocket)
        
        # Clean up failed connections
        for websocket in failed_connections:
            self.disconnect(websocket)
        
        if failed_connections:
            logger.debug(f"Cleaned up {len(failed_connections)} dead connections during heartbeat")
    
    async def _cleanup_dead_connections(self) -> None:
        """Clean up connections that haven't responded to heartbeats."""
        if not self.connection_metadata:
            return
        
        cutoff_time = datetime.utcnow() - timedelta(seconds=self.heartbeat_timeout)
        dead_connections = []
        
        for websocket, conn_info in self.connection_metadata.items():
            if conn_info.last_heartbeat < cutoff_time:
                dead_connections.append(websocket)
        
        for websocket in dead_connections:
            conn_info = self.connection_metadata[websocket]
            logger.info(f"Cleaning up dead connection for user {conn_info.user_id} "
                       f"(last heartbeat: {conn_info.last_heartbeat})")
            self.disconnect(websocket)


# Global WebSocket manager instance
websocket_manager = WebSocketManager()


def get_websocket_manager() -> WebSocketManager:
    """
    Dependency function to get the WebSocket manager instance.
    
    Returns:
        WebSocketManager: The global WebSocket manager instance
    """
    return websocket_manager