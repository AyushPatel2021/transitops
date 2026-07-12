from datetime import date

from backend.core import fields
from backend.core.exceptions import UserError
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
    _name_field_ = "rec_name"
    _description_ = "Fuel Log"

    vehicle_id = fields.Many2one("vehicle", label="Vehicle", required=True)
    trip_id = fields.Many2one("trip", label="Trip")
    liters = fields.Float(label="Liters", required=True)
    cost = fields.Float(label="Cost", required=True)
    date = fields.Date(label="Date", required=True, default=date.today)
    odometer_reading = fields.Float(label="Odometer Reading")
    rec_name = fields.Char(label="Reference", compute="_compute_rec_name", store=False, readonly=True)

    def _compute_rec_name(self):
        vehicle = getattr(self, "vehicle", None)
        reg = getattr(vehicle, "registration_number", None) if vehicle else None
        date_str = str(self.date) if self.date else ""
        liters_str = f"{self.liters:.1f}L" if self.liters is not None else ""
        parts = [p for p in [reg, date_str, liters_str] if p]
        self.rec_name = " / ".join(parts) if parts else f"Fuel Log #{self.id or 'New'}"

    def __getattr__(self, name):
        if name == "rec_name":
            vehicle = object.__getattribute__(self, "__dict__").get("vehicle") or getattr(self, "vehicle", None)
            reg = getattr(vehicle, "registration_number", None) if vehicle else None
            try:
                date_val = object.__getattribute__(self, "date")
            except AttributeError:
                date_val = None
            try:
                liters_val = object.__getattribute__(self, "liters")
            except AttributeError:
                liters_val = None
            date_str = str(date_val) if date_val else ""
            liters_str = f"{liters_val:.1f}L" if liters_val is not None else ""
            parts = [p for p in [reg, date_str, liters_str] if p]
            return " / ".join(parts) if parts else f"Fuel Log #{getattr(self, 'id', 'New')}"
        raise AttributeError(name)

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

    @classmethod
    def create(cls, db, vals, **kwargs):
        cls._validate_values(vals)
        return super().create(db, vals, **kwargs)

    def write(self, *args, **kwargs):
        vals = args[1] if len(args) == 2 else args[0] if args else kwargs.get("vals", {})
        self._validate_values(vals)
        return super().write(*args, **kwargs)

    @staticmethod
    def _validate_values(vals):
        if "liters" in vals and vals["liters"] is not None and float(vals["liters"]) < 0:
            raise UserError("Fuel liters cannot be negative.")
        if "cost" in vals and vals["cost"] is not None and float(vals["cost"]) < 0:
            raise UserError("Fuel cost cannot be negative.")
