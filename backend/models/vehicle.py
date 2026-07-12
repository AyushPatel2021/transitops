from backend.core import fields
from backend.core.exceptions import UserError
from backend.core.znova_model import ZnovaModel
from backend.models.transitops_common import ADMIN_ALL
from backend.models.transitops_common import READ_ALL
from backend.models.transitops_common import ROLE_ADMIN
from backend.models.transitops_common import ROLE_DRIVER
from backend.models.transitops_common import ROLE_FINANCE
from backend.models.transitops_common import ROLE_FLEET
from backend.models.transitops_common import ROLE_SAFETY
from backend.models.transitops_common import get_action_role_name
from backend.models.transitops_common import notify


class Vehicle(ZnovaModel):
    __tablename__ = "vehicles"
    _model_name_ = "vehicle"
    _name_field_ = "registration_number"
    _status_field_ = "status"
    _description_ = "Vehicle"

    registration_number = fields.Char(label="Registration Number", required=True, unique=True, size=80, tracking=True)
    name_model = fields.Char(label="Name / Model", required=True, size=120, tracking=True)
    type = fields.Selection([("Van", "Van"), ("Truck", "Truck"), ("Trailer", "Trailer"), ("Bike", "Bike")], label="Type", required=True, tracking=True)
    max_load_capacity = fields.Float(label="Max Load Capacity (kg)", required=True, tracking=True)
    odometer = fields.Float(label="Odometer (km)", required=True, default=0, tracking=True)
    acquisition_cost = fields.Float(label="Acquisition Cost", required=True, tracking=True)
    status = fields.Selection(
        [("available", "Available"), ("on_trip", "On Trip"), ("in_shop", "In Shop"), ("retired", "Retired")],
        label="Status",
        required=True,
        default="available",
        readonly=True,
        tracking=True,
    )
    region_id = fields.Many2one("region", label="Region", domain="[('active', '=', True)]")

    _role_permissions = {
        ROLE_ADMIN: ADMIN_ALL,
        ROLE_FLEET: ADMIN_ALL,
        ROLE_DRIVER: READ_ALL,
        ROLE_SAFETY: READ_ALL,
        ROLE_FINANCE: READ_ALL,
    }

    _ui_views = {
        "list": {
            "fields": ["registration_number", "name_model", "type", "max_load_capacity", "odometer", "status", "region_id"],
            "search_fields": ["registration_number", "name_model", "type", "status", "region_id"],
        },
        "form": {
            "show_audit_log": True,
            "groups": [
                {"title": "Vehicle", "fields": ["registration_number"], "position": "header"},
            ],
            "tabs": [
                {
                    "title": "Fleet Details",
                    "groups": [
                        {"title": "Identity", "fields": ["name_model", "type"]},
                        {"title": "Assignment", "fields": ["region_id"]},
                        {"title": "Capacity", "fields": ["max_load_capacity", "odometer"]},
                    ],
                },
                {
                    "title": "Financials",
                    "groups": [
                        {"title": "Acquisition", "fields": ["acquisition_cost"]},
                    ],
                },
            ],
            "header_buttons": [
                {"name": "retire", "label": "Retire Vehicle", "type": "secondary", "method": "action_retire", "invisible": "[('status', '=', 'retired')]"},
                {"name": "reactivate", "label": "Reactivate", "type": "primary", "method": "action_reactivate", "invisible": "[('status', '!=', 'retired')]"},
            ],
        },
    }

    _search_config = {
        "filters": [
            {"name": "available", "label": "Available", "domain": "[('status', '=', 'available')]"},
            {"name": "active", "label": "Active Fleet", "domain": "[('status', '!=', 'retired')]"},
        ],
        "group_by": [
            {"name": "by_status", "label": "By Status", "field": "status"},
            {"name": "by_region", "label": "By Region", "field": "region_id"},
        ],
    }

    def _assert_fleet_role(self):
        role = get_action_role_name(self)
        if role not in (ROLE_ADMIN, ROLE_FLEET):
            raise UserError("Only Fleet Manager or Admin can change vehicle lifecycle status.")

    def action_retire(self):
        self._assert_fleet_role()
        if self.status == "on_trip":
            raise UserError("Cannot retire a vehicle with an active trip.")
        self.write({"status": "retired"})
        return notify("Vehicle Retired", f"{self.registration_number} has been retired.")

    def action_reactivate(self):
        self._assert_fleet_role()
        self.write({"status": "available"})
        return notify("Vehicle Reactivated", f"{self.registration_number} is now available.")

    def unlink(self, *args, **kwargs):
        history_checks = (
            ("trip", "vehicle_id"),
            ("maintenance.log", "vehicle_id"),
            ("fuel.log", "vehicle_id"),
            ("expense", "vehicle_id"),
        )
        for model_name, field_name in history_checks:
            if self.env[model_name].search([(field_name, "=", self.id)], limit=1):
                raise UserError("Cannot delete a vehicle with operational history. Retire it instead.")
        return super().unlink(*args, **kwargs)
