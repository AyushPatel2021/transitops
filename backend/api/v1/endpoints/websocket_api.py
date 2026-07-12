"""
WebSocket API endpoints for real-time notifications.

This module provides WebSocket endpoints for establishing real-time connections
with authenticated users for notification delivery.
"""

import json
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.base_model import Environment
from backend.core.websocket_manager import get_websocket_manager, WebSocketManager
from backend.services.auth_service import validate_jwt_token, extract_user_claims_from_jwt

logger = logging.getLogger(__name__)

router = APIRouter()


async def authenticate_websocket_user(token: str, db: Session) -> Optional[dict]:
    """
    Authenticate user for WebSocket connection using enhanced JWT token.
    
    Args:
        token: JWT token from query parameter
        db: Database session
        
    Returns:
        dict: User information if authenticated, None otherwise
    """
    try:
        # Validate the JWT token and extract claims
        claims = validate_jwt_token(token)
        
        user_email = claims.get("sub")
        user_id = claims.get("user_id")
        is_active = claims.get("is_active", True)
        
        if not user_email or not user_id:
            logger.warning("WebSocket token missing required claims")
            return None
            
        if not is_active:
            logger.warning(f"WebSocket connection rejected for inactive user: {user_email}")
            return None
        
        env = Environment(db)
        # Get user from database to verify current status
        user = env['user'].search([('email', '=', user_email)], limit=1)
        
        if not user or not user.is_active:
            logger.warning(f"User not found or inactive: {user_email}")
            return None
        
        return {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.name if user.role else "user"
        }
        
    except Exception as e:
        logger.warning(f"WebSocket authentication failed: {e}")
        return None


@router.websocket("/ws/notifications")
async def websocket_notifications_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT authentication token"),
    websocket_manager: WebSocketManager = Depends(get_websocket_manager),
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time notifications.
    
    This endpoint establishes a WebSocket connection for authenticated users
    to receive real-time notifications. The connection requires a valid JWT token
    passed as a query parameter.
    
    Query Parameters:
        token: JWT authentication token
        
    WebSocket Message Format:
        Incoming (Client to Server):
        {
            "type": "heartbeat" | "mark_read",
            "data": {
                "notification_id": "string" (for mark_read)
            }
        }
        
        Outgoing (Server to Client):
        {
            "type": "notification" | "heartbeat" | "heartbeat_response" | "connection_established",
            "data": {...},
            "timestamp": "ISO datetime string"
        }
    """
    logger.debug(f"WebSocket connection attempt from {websocket.client}")
    logger.debug(f"Token provided: {token[:20]}..." if token else "No token provided")
    
    # Authenticate the user
    user_info = await authenticate_websocket_user(token, db)
    if not user_info:
        logger.error("❌ WebSocket authentication failed")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Authentication failed")
        return
    
    user_id = user_info["id"]
    user_email = user_info["email"]
    
    logger.debug(f"WebSocket user authenticated: {user_id} ({user_email})")
    
    # Attempt to connect
    logger.debug(f"Attempting to register WebSocket connection for user {user_id}")
    connection_success = await websocket_manager.connect(websocket, user_id, user_email)
    if not connection_success:
        logger.error(f"❌ Failed to register WebSocket connection for user {user_id}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Connection failed")
        return
    
    logger.info(f"WebSocket connected: user {user_id}")
    
    try:
        # Main message handling loop
        while True:
            try:
                # Wait for message from client
                logger.debug(f"⏳ Waiting for message from user {user_id}")
                data = await websocket.receive_text()
                logger.debug(f"📨 Received message from user {user_id}: {data}")
                
                # Parse the message
                try:
                    message_data = json.loads(data)
                except json.JSONDecodeError as e:
                    logger.warning(f"❌ Invalid JSON from user {user_id}: {e}")
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "data": {
                            "message": "Invalid JSON format"
                        }
                    }))
                    continue
                
                # Handle the message
                logger.debug(f"🔄 Processing message from user {user_id}: {message_data.get('type', 'unknown')}")
                await websocket_manager.handle_client_message(websocket, message_data)
                
            except WebSocketDisconnect:
                logger.debug(f"WebSocket disconnected: user {user_id}")
                break
            except Exception as e:
                logger.error(f"❌ Error handling WebSocket message for user {user_id}: {e}")
                # Try to send error message to client
                try:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "data": {
                            "message": "Internal server error"
                        }
                    }))
                except:
                    # If we can't send error message, connection is likely broken
                    logger.error(f"💥 Cannot send error message to user {user_id}, connection broken")
                    break
    
    except Exception as e:
        logger.error(f"💥 Unexpected error in WebSocket connection for user {user_id}: {e}")
    
    finally:
        # Clean up the connection
        logger.debug(f"Cleaning up WebSocket connection for user {user_id}")
        websocket_manager.disconnect(websocket)
        logger.debug(f"WebSocket cleanup completed for user {user_id}")


@router.websocket("/ws/user-data")
async def websocket_user_data_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT authentication token"),
    websocket_manager: WebSocketManager = Depends(get_websocket_manager),
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time user data synchronization.
    
    This endpoint establishes a WebSocket connection for authenticated users
    to receive real-time updates about their user data, role changes, and
    other account-related events.
    
    Query Parameters:
        token: JWT authentication token
        
    WebSocket Message Format:
        Incoming (Client to Server):
        {
            "type": "heartbeat" | "ping",
            "data": {}
        }
        
        Outgoing (Server to Client):
        {
            "type": "user_data_updated" | "user_preferences_updated" | "user_role_changed" | "user_deactivated" | "force_logout",
            "data": {...},
            "timestamp": "ISO datetime string"
        }
    """
    logger.debug(f"User data WebSocket connection attempt from {websocket.client}")
    
    # Authenticate the user
    user_info = await authenticate_websocket_user(token, db)
    if not user_info:
        logger.error("❌ User data WebSocket authentication failed")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Authentication failed")
        return
    
    user_id = user_info["id"]
    user_email = user_info["email"]
    
    logger.debug(f"User data WebSocket authenticated: {user_id} ({user_email})")
    
    # Attempt to connect
    connection_success = await websocket_manager.connect(websocket, user_id, user_email)
    if not connection_success:
        logger.error(f"❌ Failed to register user data WebSocket connection for user {user_id}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Connection failed")
        return
    
    logger.info(f"User data WebSocket connected: user {user_id}")
    
    try:
        # Send initial connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "data": {
                "user_id": user_id,
                "message": "User data WebSocket connected",
                "features": ["user_data_updates", "preference_sync", "role_changes", "multi_tab_sync"]
            },
            "timestamp": datetime.utcnow().isoformat()
        }))
        
        # Main message handling loop
        while True:
            try:
                # Wait for message from client
                data = await websocket.receive_text()
                logger.debug(f"📨 Received user data message from user {user_id}: {data}")
                
                # Parse the message
                try:
                    message_data = json.loads(data)
                except json.JSONDecodeError as e:
                    logger.warning(f"❌ Invalid JSON from user {user_id}: {e}")
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "data": {
                            "message": "Invalid JSON format"
                        }
                    }))
                    continue
                
                # Handle basic messages (heartbeat, ping)
                message_type = message_data.get("type")
                if message_type in ["heartbeat", "ping"]:
                    await websocket.send_text(json.dumps({
                        "type": "pong" if message_type == "ping" else "heartbeat_response",
                        "data": {
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    }))
                else:
                    logger.debug(f"🔄 Unknown user data message type: {message_type}")
                
            except WebSocketDisconnect:
                logger.debug(f"User data WebSocket disconnected: user {user_id}")
                break
            except Exception as e:
                logger.error(f"❌ Error handling user data WebSocket message for user {user_id}: {e}")
                break
    
    except Exception as e:
        logger.error(f"💥 Unexpected error in user data WebSocket connection for user {user_id}: {e}")
    
    finally:
        # Clean up the connection
        logger.debug(f"Cleaning up user data WebSocket for user {user_id}")
        websocket_manager.disconnect(websocket)
        logger.debug(f"User data WebSocket cleanup completed for user {user_id}")


@router.get("/ws/stats")
async def get_websocket_stats(
    websocket_manager: WebSocketManager = Depends(get_websocket_manager)
):
    """
    Get WebSocket connection statistics.
    
    Returns:
        dict: Connection statistics including total connections, unique users, etc.
    """
    return websocket_manager.get_connection_stats()