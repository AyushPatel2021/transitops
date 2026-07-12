from backend.core.znova_model import ZnovaModel
from backend.core import fields

class Timezone(ZnovaModel):
    __tablename__ = "timezones"
    _model_name_ = "timezone"
    _name_field_ = "name"
    _description_ = "Timezone"

    name = fields.Char(label="Timezone Name", required=True, size=100, help="Timezone identifier (e.g., UTC, America/New_York)")
    display_name = fields.Char(label="Display Name", required=True, size=150, help="Human-readable timezone name")
    offset = fields.Char(label="UTC Offset", size=10, help="Current UTC offset (e.g., +05:30, -08:00)")
    
    _role_permissions = {
        "admin": {"create": True, "read": True, "write": True, "delete": True},
        "user": {"create": False, "read": True, "write": False, "delete": False}
    }

    _ui_views = {
        "list": {
            "fields": ["name", "display_name", "offset"]
        },
        "form": {
            "groups": [
                {
                    "title": "Timezone Information",
                    "fields": ["name", "display_name", "offset"]
                }
            ]
        }
    }
