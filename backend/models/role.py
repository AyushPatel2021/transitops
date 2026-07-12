from backend.core.znova_model import ZnovaModel
from backend.core import fields

class Role(ZnovaModel):
    __tablename__ = "roles"
    _model_name_ = "role"
    
    name = fields.Char(label="Role Name", required=True, size=50)
    description = fields.Char(label="Description", size=200)
    permissions = fields.JSON(label="Model Permissions", default=dict)
    domain_rules = fields.JSON(label="Domain Rules", default=dict)
    
    # Reverse relation
    users = fields.One2many("user", "role_id", label="Users", show_label=True)

    def get_model_permissions(self, model_name):
        """Get CRUD permissions for a specific model"""
        return self.permissions.get(model_name, {
            "create": False,
            "read": False, 
            "write": False,
            "delete": False
        })
    
    def get_domain_rule(self, model_name):
        """Get domain rule for filtering records of a specific model"""
        return self.domain_rules.get(model_name, [])
    
    def has_permission(self, model_name, action):
        """Check if role has specific permission on model"""
        perms = self.get_model_permissions(model_name)
        return perms.get(action, False)

    # Model-level role permissions for Role management
    _role_permissions = {
        "admin": {
            "create": True,
            "read": True,
            "write": True,
            "delete": True,
            "domain": []  # Can manage all roles
        },
        "user": {
            "create": False,
            "read": True,
            "write": False,
            "delete": False,
            "domain": []  # Can see all roles but not modify
        }
    }

    _ui_views = {
        "form": {
            "groups": [
                {
                    "title": "Basic Information",
                    "fields": ["name", "description"]
                }
            ],
            "header_buttons": [
                {
                    "name": "view_users",
                    "label": "View Users",
                    "type": "primary",
                    "method": "action_view_users"
                },
                {
                    "name": "duplicate_role",
                    "label": "Duplicate Role",
                    "type": "secondary",
                    "method": "action_duplicate_role"
                }
            ],
            "tabs": [
                {
                    "title": "Permissions",
                    "fields": ["permissions"]
                },
                {
                    "title": "Domain Rules",
                    "fields": ["domain_rules"]
                },
                {
                    "title": "Statistics",
                    "fields": ["users"],
                    "readonly": True
                }
            ],
            "smart_buttons": [
                {
                    "name": "users",
                    "label": "Users",
                    "icon": "Users",
                    "field": "users",
                    "method": "action_view_users"
                }
            ]
        },
        "list": {
            "fields": ["name", "description"],
            "search_fields": ["name", "description"]
        }
    }

    def action_view_users(self):
        """Action to view users with this role"""
        return {
            "type": "ir.actions.act_window",
            "res_model": "user",
            "view_mode": "list,form",
            "domain": [("role_id", "=", self.id)],
            "name": f"Users with {self.name} role"
        }

    def action_duplicate_role(self):
        """Action to duplicate this role"""
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Duplicate Role",
                "message": f"Role duplication functionality would create a copy of {self.name}",
                "type": "info"
            }
        }
