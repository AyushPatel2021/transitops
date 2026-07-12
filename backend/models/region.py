from backend.core import fields
from backend.core.znova_model import ZnovaModel
from backend.models.transitops_common import ADMIN_ALL
from backend.models.transitops_common import READ_ALL
from backend.models.transitops_common import ROLE_ADMIN
from backend.models.transitops_common import ROLE_DRIVER
from backend.models.transitops_common import ROLE_FINANCE
from backend.models.transitops_common import ROLE_FLEET
from backend.models.transitops_common import ROLE_SAFETY


class Region(ZnovaModel):
    __tablename__ = "regions"
    _model_name_ = "region"
    _name_field_ = "name"
    _description_ = "Region"

    name = fields.Char(label="Name", required=True, unique=True, size=100, tracking=True)
    code = fields.Char(label="Code", required=True, unique=True, size=20, tracking=True)
    active = fields.Boolean(label="Active", required=True, default=True, tracking=True)

    _role_permissions = {
        ROLE_ADMIN: ADMIN_ALL,
        ROLE_FLEET: {"create": True, "read": True, "write": True, "delete": False, "domain": []},
        ROLE_DRIVER: READ_ALL,
        ROLE_SAFETY: READ_ALL,
        ROLE_FINANCE: READ_ALL,
    }

    _ui_views = {
        "list": {"fields": ["name", "code", "active"], "search_fields": ["name", "code"]},
        "form": {
            "groups": [
                {"title": "Region", "fields": ["name"], "position": "header"},
            ],
            "tabs": [
                {
                    "title": "General",
                    "groups": [
                        {"title": "Identity", "fields": ["code", "active"]},
                    ],
                },
            ],
        },
    }
