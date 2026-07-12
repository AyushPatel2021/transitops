from backend.core.znova_model import ZnovaModel
from backend.core import fields

class ActivityLog(ZnovaModel):
    __tablename__ = "activity_logs"
    _model_name_ = "activity"
    
    reference_type = fields.Char(label="Type", required=True, size=50) # equipment, request
    reference_id = fields.Integer(label="ID", required=True)
    action = fields.Char(label="Action", required=True, size=100)
    performed_by_id = fields.Many2one("user", label="User", required=True)

    _ui_views = {
        "list": {
            "fields": ["reference_type", "reference_id", "action", "performed_by_id", "created_at"],
            "search_fields": ["reference_type", "action"]
        }
    }

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
            "read": True,
            "write": False,
            "delete": False,
            "domain": [("performed_by_id", "=", "user.id")]  # Only own activity
        }
    }
