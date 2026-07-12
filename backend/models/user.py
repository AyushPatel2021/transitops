from datetime import datetime
from backend.core.znova_model import ZnovaModel
from backend.core import fields, api
from backend.core.exceptions import ValidationError
import re
import logging

logger = logging.getLogger(__name__)

class User(ZnovaModel):
    __tablename__ = "users"
    _model_name_ = "user"
    
    # Metadata for record display and state tracking
    _name_field_ = "full_name"    # Used for headers, breadcrumbs, and Many2one labels
    _status_field_ = "theme"   # Used for status banners and state-based logic
    
    # Core fields
    full_name = fields.Char(label="Full Name", required=True, size=100, tracking=True)
    email = fields.Char(label="Email Address", required=True, size=100, help="User's login email address", tracking=True)
    hashed_password = fields.Char(label="Password", required=True, size=200, invisible="[('id', '!=', False)]", tracking=True)
    is_active = fields.Boolean(label="Active", default=True, help="Whether the user account is active", tracking=True)
    
    # Relations
    role_id = fields.Many2one("role", label="Role", required=True, help="User's role determines their permissions", tracking=True)
    
    # Profile & Preferences
    image = fields.Image(label="Profile Picture", max_size=2097152, tracking=True)
    last_login_at = fields.DateTime(label="Last Login", readonly=True)
    show_notification_toasts = fields.Boolean(label="Show Notification Toasts", default=True, tracking=True)
    timezone_id = fields.Many2one("timezone", label="Timezone", help="User's timezone for displaying dates and times", tracking=True, required=True)
    theme = fields.Selection([
        ("light", "Light"),
        ("dark", "Dark")
    ], label="Theme", default="dark", tracking=True)
    
    # Domain context
    def get_domain_context(self):
        """Get user context for domain rule evaluation"""
        return {
            'id': self.id,
            'role_id': self.role_id,
            'role_name': self.role.name if self.role else None,
            'is_active': self.is_active
        }

    # Model-level role permissions for User management
    _role_permissions = {
        "admin": {
            "create": True,
            "read": True,
            "write": True,
            "delete": True,
            "domain": []  # Can manage all users
        },
        "user": {
            "create": False,
            "read": True,
            "write": True,
            "delete": False,
            "domain": [("id", "=", "user.id")]  # Only their own record
        }
    }

    _search_config = {
        "filters": [
            {
                "name": "active",
                "label": "Active Users",
                "domain": "[('is_active', '=', True)]"
            },
            {
                "name": "inactive",
                "label": "Inactive Users",
                "domain": "[('is_active', '=', False)]"
            },
            {
                "name": "recent_login",
                "label": "Recently Logged In (Last 7 Days)",
                "domain": "[('last_login_at', '>=', datetime.now() - timedelta(days=7))]"
            },
            {
                "name": "never_logged_in",
                "label": "Never Logged In",
                "domain": "[('last_login_at', '=', None)]"
            }
        ],
        "group_by": [
            {
                "name": "by_role",
                "label": "By Role",
                "field": "role_id"
            },
            {
                "name": "by_status",
                "label": "By Active Status",
                "field": "is_active"
            },
            {
                "name": "by_theme",
                "label": "By Theme Preference",
                "field": "theme"
            }
        ]
    }

    _ui_views = {
        "form": {
            "show_audit_log": True,
            "groups": [
                {
                    "title": "Title Information",
                    "fields": ["full_name"],
                    "position": "header"
                },
                {
                    "title": "User Information",
                    "fields": ["email", "is_active"]
                },
                {
                    "title": "Access Control",
                    "fields": ["role_id", "last_login_at"],
                },
                {
                    "title": "Preferences",
                    "fields": ["show_notification_toasts", "timezone_id", "theme"]
                },
                {
                    "title": "Authentication",
                    "fields": ["hashed_password"],
                    "invisible": "[('id', '!=', False)]"  # Only show on create
                },
                {
                    "title": "Profile Picture",
                    "fields": ["image"],
                    "position": "header"
                }
            ],
            "header_buttons": [
                {
                    "name": "reset_password",
                    "label": "Reset Password",
                    "type": "secondary",
                    "method": "action_reset_password",
                    "invisible": "[('id', '=', False)]"  # Only show on existing records
                },
                {
                    "name": "toggle_active",
                    "label": "Toggle Active Status",
                    "type": "secondary", 
                    "method": "action_toggle_active"
                }
            ]
        },
        "list": {
            "fields": ["full_name", "email", "role_id", "is_active", "last_login_at"],
            "search_fields": ["full_name", "email", "role_id"]
        }
    }

    @api.model
    def default_get(cls, fields_list):
        """Set default values including UTC timezone"""
        res = super(User, cls).default_get(fields_list)
        
        # Set default timezone to UTC if timezone_id is in the fields list
        if 'timezone_id' in fields_list and not res.get('timezone_id'):
            try:
                # Get the environment from the class
                from backend.core.base_model import Environment
                from backend.core.database import SessionLocal
                
                db = SessionLocal()
                try:
                    env = Environment(db)
                    # Find UTC timezone record
                    utc_timezone = env['timezone'].search([('name', '=', 'UTC')], limit=1)
                    if utc_timezone:
                        res['timezone_id'] = utc_timezone[0].id
                finally:
                    db.close()
            except Exception as e:
                logger.warning(f"Could not set default UTC timezone: {e}")
        
        return res

    def action_reset_password(self):
        """Action to reset user password"""
        return {
            "type": "ir.actions.client",
            "tag": "reset_password_modal",
            "params": {
                "user_id": self.id,
                "user_name": self.full_name,
                "user_email": self.email
            }
        }

    def action_toggle_active(self):
        """Action to toggle user active status"""
        self.is_active = not self.is_active
        status = "activated" if self.is_active else "deactivated"
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "User Status Updated",
                "message": f"User {self.full_name} has been {status}",
                "type": "success",
                "refresh": True
            }
        }

    @property
    def role_display(self):
        """Display role information"""
        if self.role:
            return f"{self.role.name} - {self.role.description}"
        return "No role assigned"

    def update_last_login(self):
        """Update the last login timestamp"""
        self.write({'last_login_at': datetime.utcnow()})
    
    def get_formatted_last_login(self, format_type: str = 'default') -> str:
        """Get formatted last login time"""
        if not self.last_login_at:
            return "Never"
        
        return self.last_login_at.strftime('%Y-%m-%d %H:%M:%S')
    
    def to_dict(self, fields=None, user_role=None, include_domain_states=False, user_context=None, include_relations=True, max_depth=1):
        """Override to_dict to include formatted dates"""
        data = super().to_dict(fields=fields, user_role=user_role, include_domain_states=include_domain_states, user_context=user_context, max_depth=max_depth)
        
        # Format datetime fields simply
        if self.last_login_at:
            data['last_login_at_formatted'] = self.last_login_at.strftime('%Y-%m-%d %H:%M:%S')
        
        if hasattr(self, 'created_at') and self.created_at:
            data['created_at_formatted'] = self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        
        if hasattr(self, 'updated_at') and self.updated_at:
            data['updated_at_formatted'] = self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        
        return data
    
    @classmethod
    def _validate_password(cls, password: str):
        """Validate password requirements"""
        if not password:
            raise ValidationError("Password is required")
        
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long")
        
        if not re.search(r'[A-Za-z]', password):
            raise ValidationError("Password must contain at least one letter")
        
        if not re.search(r'\d', password):
            raise ValidationError("Password must contain at least one number")
    
    @classmethod
    def create(cls, db, vals: dict):
        """Override create to add password validation"""
        # Validate password if provided
        if 'hashed_password' in vals and vals['hashed_password']:
            pwd = vals['hashed_password']
            
            # If it's already a bcrypt hash (e.g. from DataLoader $P$), don't hash again
            if not pwd.startswith('$2b$'):
                cls._validate_password(pwd)
                
                # Hash the password
                from backend.services.auth_service import get_password_hash
                vals['hashed_password'] = get_password_hash(pwd)
        return super().create(db, vals)

    @classmethod
    def check_pending_notifications(cls, db):
        """
        Cron function: Check and process pending notifications.
        This function will be called by the cron system hourly.
        """
        from datetime import timedelta
        try:
            env = Environment(db)
            active_users = env['user'].search([('is_active', '=', True)])
            
            logger.info(f"Starting notification check for {len(active_users)} active users")
            
            processed_count = 0
            notifications_found = 0
            
            for user in active_users:
                try:
                    # Check for unread notifications for this user
                    unread_notifications = env['notification'].search([
                        ('user_id', '=', user.id),
                        ('read', '=', False),
                        ('created_at', '>=', datetime.now() - timedelta(hours=24))
                    ])
                    
                    if unread_notifications:
                        notifications_found += len(unread_notifications)
                        
                        # Check if user hasn't logged in recently (more than 1 day)
                        if user.last_login_at and user.last_login_at < datetime.now() - timedelta(days=1):
                            logger.info(f"User {user.full_name} has {len(unread_notifications)} unread notifications and hasn't logged in since {user.last_login_at}")
                        
                        # Log urgent notifications
                        urgent_notifications = unread_notifications.filtered(lambda n: n.type == "danger")
                        if urgent_notifications:
                            logger.warning(f"User {user.full_name} has {len(urgent_notifications)} urgent unread notifications")
                    
                    processed_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to check notifications for user {user.full_name}: {e}")
                    continue
            
            result_message = f"Notification check completed. Processed {processed_count} users, found {notifications_found} unread notifications"
            logger.info(result_message)
            
            return {
                "success": True,
                "message": result_message,
                "users_processed": processed_count,
                "notifications_found": notifications_found
            }
            
        except Exception as e:
            error_message = f"Error in notification check task: {str(e)}"
            logger.error(error_message)
            return {
                "success": False,
                "message": error_message,
                "error": str(e)
            }
