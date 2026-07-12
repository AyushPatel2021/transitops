from datetime import datetime

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
from backend.models.transitops_common import notify


class Trip(ZnovaModel):
    __tablename__ = "trips"
    _model_name_ = "trip"
    _name_field_ = "destination"
    _status_field_ = "status"
    _description_ = "Trip"

    source = fields.Char(label="Source", required=True, size=120, tracking=True)
    destination = fields.Char(label="Destination", required=True, size=120, tracking=True)
    vehicle_id = fields.Many2one("vehicle", label="Vehicle", required=True, domain="[('status', '=', 'available')]", tracking=True)
    driver_id = fields.Many2one("driver", label="Driver", required=True, domain="[('status', '=', 'available')]", tracking=True)
    cargo_weight = fields.Float(label="Cargo Weight (kg)", required=True, tracking=True)
    planned_distance = fields.Float(label="Planned Distance (km)", required=True)
    actual_distance = fields.Float(label="Actual Distance (km)")
    fuel_consumed = fields.Float(label="Fuel Consumed (L)")
    final_odometer = fields.Float(label="Final Odometer")
    status = fields.Selection(
        [("draft", "Draft"), ("dispatched", "Dispatched"), ("completed", "Completed"), ("cancelled", "Cancelled")],
        label="Status",
        required=True,
        default="draft",
        readonly=True,
        tracking=True,
    )
    created_by = fields.Many2one("user", label="Created By", required=True, readonly=True)
    dispatched_at = fields.DateTime(label="Dispatched At", readonly=True)
    completed_at = fields.DateTime(label="Completed At", readonly=True)

    _role_permissions = {
        ROLE_ADMIN: ADMIN_ALL,
        ROLE_FLEET: ADMIN_ALL,
        ROLE_DRIVER: {
            "create": True,
            "read": True,
            "write": True,
            "delete": True,
            "domain": ["|", ("created_by", "=", "user.id"), ("driver_id.user_id", "=", "user.id")],
        },
        ROLE_SAFETY: READ_ALL,
        ROLE_FINANCE: READ_ALL,
    }

    _ui_views = {
        "list": {
            "fields": ["source", "destination", "vehicle_id", "driver_id", "cargo_weight", "status", "created_by"],
            "search_fields": ["source", "destination", "vehicle_id", "driver_id", "status"],
        },
        "form": {
            "show_audit_log": True,
            "groups": [
                {"title": "Trip", "fields": ["source"], "position": "header"},
                {"title": "Audit", "fields": ["created_by", "dispatched_at", "completed_at"], "position": "right"},
            ],
            "tabs": [
                {
                    "title": "Dispatch",
                    "groups": [
                        {"title": "Assignment", "fields": ["vehicle_id", "driver_id"]},
                        {"title": "Cargo & Route", "fields": ["destination", "cargo_weight", "planned_distance"]},
                    ],
                },
                {
                    "title": "Completion",
                    "groups": [
                        {"title": "Final Readings", "fields": ["actual_distance", "fuel_consumed", "final_odometer"]},
                    ],
                },
            ],
            "header_buttons": [
                {"name": "dispatch", "label": "Dispatch", "type": "primary", "method": "action_dispatch", "invisible": "[('status', '!=', 'draft')]"},
                {"name": "complete", "label": "Complete Trip", "type": "primary", "method": "action_complete", "invisible": "[('status', '!=', 'dispatched')]"},
                {"name": "cancel", "label": "Cancel", "type": "secondary", "method": "action_cancel", "invisible": "[('status', 'in', ['completed', 'cancelled'])]"},
            ],
        },
    }

    _search_config = {
        "filters": [
            {"name": "draft", "label": "Draft", "domain": "[('status', '=', 'draft')]"},
            {"name": "active", "label": "Active", "domain": "[('status', '=', 'dispatched')]"},
            {"name": "my_trips", "label": "My Trips", "domain": "['|', ('created_by', '=', user.id), ('driver_id.user_id', '=', user.id)]"},
        ],
        "group_by": [
            {"name": "by_status", "label": "By Status", "field": "status"},
            {"name": "by_vehicle", "label": "By Vehicle", "field": "vehicle_id"},
        ],
    }

    def write(self, *args, **kwargs):
        vals = args[1] if len(args) == 2 else args[0]
        merged = {
            "vehicle_id": self.vehicle.id if self.vehicle else None,
            "cargo_weight": self.cargo_weight,
        }
        merged.update(vals)
        self._validate_trip_values(merged)
        return super().write(*args, **kwargs)

    def _validate_trip_values(self, vals):
        vehicle = vals.get("vehicle_id")
        cargo = vals.get("cargo_weight")
        if isinstance(vehicle, dict):
            vehicle = vehicle.get("id")
        if vehicle and cargo is not None:
            vehicle_rec = self.env["vehicle"].browse(vehicle)
            if vehicle_rec and float(cargo) > float(vehicle_rec.max_load_capacity):
                raise UserError("Cargo weight cannot exceed vehicle max load capacity.")

    def _assert_dispatch_assets_available(self):
        if not self.vehicle or self.vehicle.status != "available":
            raise UserError("Vehicle no longer available.")
        if self.vehicle.status in ("in_shop", "retired"):
            raise UserError("Vehicle is not eligible for dispatch.")
        if not self.driver or self.driver.status != "available" or not self.driver.license_valid:
            raise UserError("Driver is not eligible for dispatch.")
        if self.cargo_weight > self.vehicle.max_load_capacity:
            raise UserError("Cargo weight cannot exceed vehicle max load capacity.")

    def action_dispatch(self):
        if self.status != "draft":
            raise UserError("Only draft trips can be dispatched.")
        self._assert_dispatch_assets_available()
        self.write({"status": "dispatched", "dispatched_at": datetime.utcnow()})
        self.vehicle.write({"status": "on_trip"})
        self.driver.write({"status": "on_trip"})
        return notify("Trip Dispatched", f"Trip to {self.destination} has been dispatched.")

    def action_complete(self):
        if self.status != "dispatched":
            raise UserError("Only dispatched trips can be completed.")
        if self.final_odometer is None or self.fuel_consumed is None:
            raise UserError("Final odometer and fuel consumed are required before completing a trip.")
        if self.final_odometer < self.vehicle.odometer:
            raise UserError("Final odometer cannot be lower than the vehicle's current odometer.")
        self.write({"status": "completed", "completed_at": datetime.utcnow()})
        self.vehicle.write({"status": "available", "odometer": self.final_odometer})
        self.driver.write({"status": "available"})
        self.env["fuel.log"].create({
            "vehicle_id": self.vehicle.id,
            "trip_id": self.id,
            "liters": self.fuel_consumed,
            "cost": 0,
            "odometer_reading": self.final_odometer,
        })
        return notify("Trip Completed", f"Trip to {self.destination} has been completed.")

    def action_cancel(self):
        if self.status not in ("draft", "dispatched"):
            raise UserError("Completed and cancelled trips are terminal.")
        was_dispatched = self.status == "dispatched"
        self.write({"status": "cancelled"})
        if was_dispatched:
            self.vehicle.write({"status": "available"})
            self.driver.write({"status": "available"})
        return notify("Trip Cancelled", f"Trip to {self.destination} has been cancelled.")
