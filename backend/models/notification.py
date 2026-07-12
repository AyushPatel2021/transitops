from datetime import datetime
from sqlalchemy.sql import func
from backend.core.znova_model import ZnovaModel
from backend.core import fields

class Notification(ZnovaModel):
    __tablename__ = "notifications"
    _model_name_ = "notification"
    
    # Core notification fields
    title = fields.Char(label="Title", required=True, size=255, help="Notification title displayed to the user")
    message = fields.Text(label="Message", required=True, help="Detailed notification message content")
    type = fields.Selection([
        ("info", "Info"),
        ("success", "Success"),
        ("warning", "Warning"),
        ("danger", "Danger")
    ], label="Type", default="info", help="Notification type determines the visual styling")
    
    # User targeting
    user_id = fields.Many2one("user", label="User", required=True, help="User who will receive this notification")
    
    # Status tracking
    read = fields.Boolean(label="Read", default=False, help="Whether the user has read this notification")
    read_at = fields.DateTime(label="Read At", readonly=True, help="Timestamp when the notification was read")
    
    # Action configuration
    action_type = fields.Selection([
        ("navigate", "Navigate"),
        ("modal", "Modal"),
        ("function", "Function")
    ], label="Action Type", help="Type of action to execute when notification is clicked")
    action_target = fields.Char(label="Action Target", size=500, help="Target URL, modal component, or function name for the action")
    action_params = fields.JSON(label="Action Parameters", help="JSON parameters for the notification action")
    
    # Metadata
    created_by = fields.Many2one("user", label="Created By", readonly=True, help="User who created this notification")
    expires_at = fields.DateTime(label="Expires At", help="When this notification expires and should be cleaned up")
    
    _ui_views = {
        "form": {
            "groups": [
                {
                    "title": "Notification Content",
                    "fields": ["title", "message", "type"]
                },
                {
                    "title": "Targeting",
                    "fields": ["user_id"]
                },
                {
                    "title": "Status",
                    "fields": ["read", "read_at"]
                },
                {
                    "title": "Action Configuration",
                    "fields": ["action_type", "action_target", "action_params"]
                },
                {
                    "title": "Metadata",
                    "fields": ["created_by", "expires_at"]
                }
            ]
        },
        "list": {
            "fields": ["title", "user_id", "type", "read", "created_at", "expires_at"],
            "search_fields": ["title", "message", "user_id", "type"]
        }
    }
    
    # Role-based permissions
    _role_permissions = {
        "admin": {
            "create": True,
            "read": True,
            "write": True,
            "delete": True,
            "domain": []  # Can manage all notifications
        },
        "user": {
            "create": False,
            "read": True,
            "write": True,  # Can mark as read
            "delete": False,
            "domain": [("user_id", "=", "user.id")]  # Only their own notifications
        }
    }
    
    def mark_as_read(self):
        """Mark this notification as read"""
        self.ensure_one()
        if not self.read:
            self.write({
                'read': True,
                'read_at': datetime.utcnow()
            })
        return True
    
    def is_expired(self):
        """Check if this notification has expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def to_websocket_message(self):
        """Convert notification to WebSocket message format"""
        return {
            "type": "notification",
            "data": {
                "action": "new",
                "notification": {
                    "id": str(self.id),
                    "title": self.title,
                    "message": self.message,
                    "type": self.type,
                    "user_id": self.user_id.id if self.user_id else None,  # Extract ID from Many2one field
                    "action": {
                        "type": self.action_type,
                        "target": self.action_target,
                        "params": self.action_params
                    } if self.action_type else None,
                    "created_at": self.created_at.isoformat() if self.created_at else None,
                    "read": self.read
                }
            }
        }
    
    @classmethod
    def cleanup_expired(cls, db):
        """Remove expired notifications"""
        env = Environment(db)
        expired = env['notification'].search([('expires_at', '<', datetime.utcnow())])
        count = len(expired)
        expired.unlink()
        return count
    
    @classmethod
    def get_unread_count(cls, db, user_id: int):
        """Get count of unread notifications for a user"""
        env = Environment(db)
        return len(env['notification'].search([
            ('user_id', '=', user_id),
            ('read', '=', False)
        ]))
    
    @classmethod
    def get_recent_notifications(cls, db, user_id: int, limit: int = 50, unread_only: bool = False):
        """Get recent notifications for a user"""
        env = Environment(db)
        domain = [('user_id', '=', user_id)]
        
        if unread_only:
            domain.append(('read', '=', False))
        
        return env['notification'].search(domain, limit=limit, order='created_at desc')
    
    @classmethod
    def mark_all_as_read(cls, db, user_id: int):
        """Mark all notifications as read for a user"""
        env = Environment(db)
        unread = env['notification'].search([
            ('user_id', '=', user_id),
            ('read', '=', False)
        ])
        count = len(unread)
        unread.write({
            'read': True,
            'read_at': datetime.utcnow()
        })
        return count