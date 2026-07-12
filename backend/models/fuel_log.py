from datetime import date

from backend.core import fields
from backend.core.znova_model import ZnovaModel
from backend.models.transitops_common import ADMIN_ALL
from backend.models.transitops_common import NO_ACCESS
from backend.models.transitops_common import ROLE_ADMIN
from backend.models.transitops_common import ROLE_DRIVER
from backend.models.transitops_common import ROLE_FINANCE
from backend.models.transitops_common import ROLE_FLEET
from backend.models.transitops_common import ROLE_SAFETY


class FuelLog(ZnovaModel):
    __tablename__ = "fuel_logs"
    _model_name_ = "fuel.log"
    _name_field_ = "vehicle_id"
    _description_ = "Fuel Log"

    vehicle_id = fields.Many2one("vehicle", label="Vehicle", required=True)
    trip_id = fields.Many2one("trip", label="Trip")
    liters = fields.Float(label="Liters", required=True)
    cost = fields.Float(label="Cost", required=True)
    date = fields.Date(label="Date", required=True, default=date.today)
    odometer_reading = fields.Float(label="Odometer Reading")

    _role_permissions = {
        ROLE_ADMIN: ADMIN_ALL,
        ROLE_FLEET: {"create": True, "read": True, "write": True, "delete": False, "domain": []},
        ROLE_DRIVER: NO_ACCESS,
        ROLE_SAFETY: NO_ACCESS,
        ROLE_FINANCE: ADMIN_ALL,
    }

    _ui_views = {
        "list": {
            "fields": ["vehicle_id", "trip_id", "liters", "cost", "date", "odometer_reading"],
            "search_fields": ["vehicle_id", "trip_id", "date"],
        },
        "form": {
            "groups": [
                {"title": "Fuel Log", "fields": ["vehicle_id", "trip_id"], "position": "header"},
            ],
            "tabs": [
                {
                    "title": "Fuel",
                    "groups": [
                        {"title": "Quantity", "fields": ["liters", "odometer_reading"]},
                        {"title": "Cost", "fields": ["cost", "date"]},
                    ],
                },
            ],
        },
    }
