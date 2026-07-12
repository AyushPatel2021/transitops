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
    vehicle_count = fields.Integer(label="Vehicle Count", compute="_compute_vehicle_count", store=False, readonly=True)
    driver_count = fields.Integer(label="Driver Count", compute="_compute_driver_count", store=False, readonly=True)

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
            "smart_buttons": [
                {
                    "name": "vehicles",
                    "label": "Vehicles",
                    "icon": "BusFront",
                    "field": "vehicle_count",
                    "method": "action_view_vehicles",
                    "groups": ["admin", "fleet_manager"],
                },
                {
                    "name": "drivers",
                    "label": "Drivers",
                    "icon": "UserRoundCheck",
                    "field": "driver_count",
                    "method": "action_view_drivers",
                    "groups": ["admin", "fleet_manager"],
                },
            ],
        },
    }

    def _compute_vehicle_count(self):
        self.vehicle_count = len(self.env["vehicle"].search([("region_id", "=", self.id)])) if self.id else 0

    def _compute_driver_count(self):
        self.driver_count = len(self.env["driver"].search([("region_id", "=", self.id)])) if self.id else 0

    def __getattr__(self, name):
        if name == "vehicle_count":
            return len(self.env["vehicle"].search([("region_id", "=", self.id)])) if self.id else 0
        if name == "driver_count":
            return len(self.env["driver"].search([("region_id", "=", self.id)])) if self.id else 0
        raise AttributeError(name)

    def action_view_vehicles(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "vehicle",
            "view_mode": "list,form",
            "domain": [("region_id", "=", self.id)],
            "name": f"Vehicles — {self.name}",
        }

    def action_view_drivers(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "driver",
            "view_mode": "list,form",
            "domain": [("region_id", "=", self.id)],
            "name": f"Drivers — {self.name}",
        }
