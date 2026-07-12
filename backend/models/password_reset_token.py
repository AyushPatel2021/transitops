from datetime import datetime, timedelta
import secrets
from backend.core.znova_model import ZnovaModel
from backend.core import fields

class PasswordResetToken(ZnovaModel):
    __tablename__ = "password_reset_tokens"
    _model_name_ = "password_reset_token"
    
    token = fields.Char(label="Token", required=True, size=255, help="Unique reset token")
    user_id = fields.Many2one("user", label="User", required=True, help="User requesting password reset")
    expires_at = fields.DateTime(label="Expires At", required=True, help="Expiration time")
    used = fields.Boolean(label="Used", default=False, help="Whether this token has been used")
    
    _role_permissions = {
        "admin": {
            "create": True,
            "read": True,
            "write": True,
            "delete": True,
            "domain": []
        },
        "user": {
            "create": False,
            "read": False,
            "write": False,
            "delete": False,
            "domain": []
        }
    }

    
    def __init__(self, **kwargs):
        if 'token' not in kwargs:
            kwargs['token'] = secrets.token_urlsafe(32)
        if 'expires_at' not in kwargs:
            kwargs['expires_at'] = datetime.utcnow() + timedelta(hours=1)
        super().__init__(**kwargs)
    
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self) -> bool:
        return not self.used and not self.is_expired()
    
    def mark_as_used(self):
        """Mark the token as used"""
        self.write({'used': True})