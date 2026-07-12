from datetime import date
from datetime import datetime

from backend.core import api
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
    driver_id = fields.Many2one(
        "driver",
        label="Driver",
        required=True,
        domain=f"[('status', '=', 'available'), ('license_expiry_date', '>=', '{date.today().isoformat()}')]",
        tracking=True,
    )
    cargo_weight = fields.Float(label="Cargo Weight (kg)", required=True, tracking=True)
    planned_distance = fields.Float(label="Planned Distance (km)", required=True)
    actual_distance = fields.Float(label="Actual Distance (km)")
    fuel_consumed = fields.Float(label="Fuel Consumed (L)")
    fuel_unit_cost = fields.Float(label="Fuel Cost (1 L)")
    revenue = fields.Float(label="Revenue")
    total_fuel_cost = fields.Float(label="Total Fuel Cost", compute="_compute_total_fuel_cost", store=False, readonly=True)
    final_odometer = fields.Float(label="Final Odometer")
    status = fields.Selection(
        [("draft", "Draft"), ("dispatched", "Dispatched"), ("completed", "Completed"), ("cancelled", "Cancelled")],
        label="Status",
        required=True,
        default="draft",
        readonly=True,
        tracking=True,
    )
    created_by = fields.Many2one("user", label="Created By", readonly=True)
    dispatched_at = fields.DateTime(label="Dispatched At", readonly=True)
    completed_at = fields.DateTime(label="Completed At", readonly=True)
    fuel_log_count = fields.Integer(label="Fuel Log Count", compute="_compute_fuel_log_count", store=False, readonly=True)

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
                        {"title": "Final Readings", "fields": ["actual_distance", "final_odometer"]},
                        {"title": "Fuel", "fields": ["fuel_consumed", "fuel_unit_cost", "total_fuel_cost"]},
                        {"title": "Revenue", "fields": ["revenue"]},
                    ],
                },
                {
                    "title": "Audit",
                    "groups": [
                        {"title": "Audit", "fields": ["created_by", "dispatched_at", "completed_at"]},
                    ],
                },
            ],
            "header_buttons": [
                {"name": "dispatch", "label": "Dispatch", "type": "primary", "method": "action_dispatch", "invisible": "[('status', '!=', 'draft')]"},
                {"name": "complete", "label": "Complete Trip", "type": "primary", "method": "action_complete", "invisible": "[('status', '!=', 'dispatched')]"},
                {"name": "cancel", "label": "Cancel", "type": "secondary", "method": "action_cancel", "invisible": "[('status', 'in', ['completed', 'cancelled'])]"},
            ],
            "smart_buttons": [
                {
                    "name": "fuel_log",
                    "label": "Fuel Log",
                    "icon": "Fuel",
                    "field": "fuel_log_count",
                    "method": "action_view_fuel_log",
                    "invisible": "[('status', '!=', 'completed')]",
                },
            ],
        },
    }

    _search_config = {
        "filters": [
            {"name": "draft", "label": "Draft", "domain": "[('status', '=', 'draft')]"},
            {"name": "dispatched", "label": "Dispatched", "domain": "[('status', '=', 'dispatched')]"},
            {"name": "completed", "label": "Completed", "domain": "[('status', '=', 'completed')]"},
            {"name": "cancelled", "label": "Cancelled", "domain": "[('status', '=', 'cancelled')]"},
            {"name": "active", "label": "Active", "domain": "[('status', '=', 'dispatched')]"},
            {"name": "my_trips", "label": "My Trips", "domain": "['|', ('created_by', '=', user.id), ('driver_id.user_id', '=', user.id)]"},
        ],
        "group_by": [
            {"name": "by_status", "label": "By Status", "field": "status"},
            {"name": "by_vehicle", "label": "By Vehicle", "field": "vehicle_id"},
            {"name": "by_driver", "label": "By Driver", "field": "driver_id"},
        ],
    }

    @classmethod
    def create(cls, db, vals, **kwargs):
        vals = vals.copy()
        user_id = kwargs.get("user_id")
        if user_id and not vals.get("created_by"):
            vals["created_by"] = user_id

        cls._validate_trip_values_for_db(db, vals)
        return super().create(db, vals, **kwargs)

    def write(self, *args, **kwargs):
        vals = args[1] if len(args) == 2 else args[0] if args else kwargs.get("vals", {})
        if (
            "status" in vals
            and vals.get("status") != self.status
            and not getattr(self, "_allow_status_transition", False)
        ):
            raise UserError("Trip status can only be changed through Dispatch, Complete, or Cancel actions.")

        merged = {
            "vehicle_id": self.vehicle.id if self.vehicle else None,
            "cargo_weight": self.cargo_weight,
            "fuel_unit_cost": self.fuel_unit_cost,
        }
        merged.update(vals)
        self._validate_trip_values(merged)
        return super().write(*args, **kwargs)

    @api.depends("fuel_consumed", "fuel_unit_cost")
    def _compute_total_fuel_cost(self):
        self.total_fuel_cost = self._get_total_fuel_cost()

    def _compute_fuel_log_count(self):
        self.fuel_log_count = len(self.env["fuel.log"].search([("trip_id", "=", self.id)])) if self.id else 0

    def _get_total_fuel_cost(self):
        if self.fuel_consumed is None or self.fuel_unit_cost is None:
            return 0.0
        return float(self.fuel_consumed) * float(self.fuel_unit_cost)

    def __getattr__(self, name):
        if name == "total_fuel_cost":
            return self._get_total_fuel_cost()
        if name == "fuel_log_count":
            return len(self.env["fuel.log"].search([("trip_id", "=", self.id)])) if self.id else 0
        raise AttributeError(name)

    def action_view_fuel_log(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "fuel.log",
            "view_mode": "list,form",
            "domain": [("trip_id", "=", self.id)],
            "name": f"Fuel Log — {self.destination}",
        }

    def _validate_trip_values(self, vals):
        vehicle = vals.get("vehicle_id")
        cargo = vals.get("cargo_weight")
        fuel_unit_cost = vals.get("fuel_unit_cost")
        if isinstance(vehicle, dict):
            vehicle = vehicle.get("id")
        if vehicle and cargo is not None:
            vehicle_rec = self.env["vehicle"].browse(vehicle)
            if vehicle_rec and float(cargo) > float(vehicle_rec.max_load_capacity):
                raise UserError("Cargo weight cannot exceed vehicle max load capacity.")
        if fuel_unit_cost is not None and float(fuel_unit_cost) < 0:
            raise UserError("Fuel cost per liter cannot be negative.")

    @classmethod
    def _validate_trip_values_for_db(cls, db, vals):
        vehicle = vals.get("vehicle_id")
        cargo = vals.get("cargo_weight")
        if isinstance(vehicle, dict):
            vehicle = vehicle.get("id")
        if vehicle and cargo is not None:
            from backend.core.base_model import Environment

            vehicle_rec = Environment(db)["vehicle"].browse(vehicle)
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
        self._allow_status_transition = True
        try:
            self.write({"status": "dispatched", "dispatched_at": datetime.utcnow()})
        finally:
            self._allow_status_transition = False
        self.vehicle.write({"status": "on_trip"})
        self.driver.write({"status": "on_trip"})
        return notify("Trip Dispatched", f"Trip to {self.destination} has been dispatched.")

    def action_complete(self):
        if self.status != "dispatched":
            raise UserError("Only dispatched trips can be completed.")
        if self.final_odometer is None or self.fuel_consumed is None or self.fuel_unit_cost is None or self.revenue is None:
            raise UserError("Final odometer, fuel consumed, fuel cost per liter, and revenue are required before completing a trip.")
        if self.final_odometer < self.vehicle.odometer:
            raise UserError("Final odometer cannot be lower than the vehicle's current odometer.")
        self._allow_status_transition = True
        try:
            self.write({"status": "completed", "completed_at": datetime.utcnow()})
        finally:
            self._allow_status_transition = False
        self.vehicle.write({"status": "available", "odometer": self.final_odometer})
        self.driver.write({"status": "available"})
        self.env["fuel.log"].create({
            "vehicle_id": self.vehicle.id,
            "trip_id": self.id,
            "liters": self.fuel_consumed,
            "cost": self.total_fuel_cost,
            "odometer_reading": self.final_odometer,
        })
        return notify("Trip Completed", f"Trip to {self.destination} has been completed.")

    def action_cancel(self):
        if self.status not in ("draft", "dispatched"):
            raise UserError("Completed and cancelled trips are terminal.")
        was_dispatched = self.status == "dispatched"
        self._allow_status_transition = True
        try:
            self.write({"status": "cancelled"})
        finally:
            self._allow_status_transition = False
        if was_dispatched:
            self.vehicle.write({"status": "available"})
            self.driver.write({"status": "available"})
        return notify("Trip Cancelled", f"Trip to {self.destination} has been cancelled.")
