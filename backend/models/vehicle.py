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
    total_operational_cost = fields.Float(label="Total Operational Cost", compute="_compute_total_operational_cost", store=False, readonly=True)
    trip_count = fields.Integer(label="Trip Count", compute="_compute_trip_count", store=False, readonly=True)
    maintenance_count = fields.Integer(label="Maintenance Count", compute="_compute_maintenance_count", store=False, readonly=True)
    fuel_log_count = fields.Integer(label="Fuel Log Count", compute="_compute_fuel_log_count", store=False, readonly=True)
    expense_count = fields.Integer(label="Expense Count", compute="_compute_expense_count", store=False, readonly=True)
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
            "fields": ["registration_number", "name_model", "type", "max_load_capacity", "odometer", "status", "region_id", "total_operational_cost"],
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
                        {"title": "Cost", "fields": ["acquisition_cost", "total_operational_cost"]},
                    ],
                },
            ],
            "header_buttons": [
                {"name": "retire", "label": "Retire Vehicle", "type": "secondary", "method": "action_retire", "invisible": "[('status', '=', 'retired')]"},
                {"name": "reactivate", "label": "Reactivate", "type": "primary", "method": "action_reactivate", "invisible": "[('status', '!=', 'retired')]"},
            ],
            "smart_buttons": [
                {
                    "name": "trips",
                    "label": "Trips",
                    "icon": "Route",
                    "field": "trip_count",
                    "method": "action_view_trips",
                },
                {
                    "name": "maintenance",
                    "label": "Maintenance",
                    "icon": "Wrench",
                    "field": "maintenance_count",
                    "method": "action_view_maintenance",
                },
                {
                    "name": "fuel_logs",
                    "label": "Fuel Logs",
                    "icon": "Fuel",
                    "field": "fuel_log_count",
                    "method": "action_view_fuel_logs",
                    "groups": ["admin", "fleet_manager", "financial_analyst"],
                },
                {
                    "name": "expenses",
                    "label": "Expenses",
                    "icon": "ReceiptText",
                    "field": "expense_count",
                    "method": "action_view_expenses",
                    "groups": ["admin", "fleet_manager", "financial_analyst"],
                },
                {
                    "name": "operational_cost",
                    "label": "Op. Cost",
                    "icon": "TrendingUp",
                    "field": "total_operational_cost",
                    "method": "action_view_fuel_logs",
                    "groups": ["admin", "fleet_manager", "financial_analyst"],
                },
            ],
        },
    }

    _search_config = {
        "filters": [
            {"name": "available", "label": "Available", "domain": "[('status', '=', 'available')]"},
            {"name": "on_trip", "label": "On Trip", "domain": "[('status', '=', 'on_trip')]"},
            {"name": "in_shop", "label": "In Shop", "domain": "[('status', '=', 'in_shop')]"},
            {"name": "retired", "label": "Retired", "domain": "[('status', '=', 'retired')]"},
            {"name": "active", "label": "Active Fleet", "domain": "[('status', '!=', 'retired')]"},
            {"name": "van", "label": "Van", "domain": "[('type', '=', 'Van')]"},
            {"name": "truck", "label": "Truck", "domain": "[('type', '=', 'Truck')]"},
            {"name": "trailer", "label": "Trailer", "domain": "[('type', '=', 'Trailer')]"},
            {"name": "bike", "label": "Bike", "domain": "[('type', '=', 'Bike')]"},
        ],
        "group_by": [
            {"name": "by_status", "label": "By Status", "field": "status"},
            {"name": "by_type", "label": "By Type", "field": "type"},
            {"name": "by_region", "label": "By Region", "field": "region_id"},
        ],
    }

    def _compute_total_operational_cost(self):
        self.total_operational_cost = self._get_total_operational_cost()

    def _compute_trip_count(self):
        self.trip_count = len(self.env["trip"].search([("vehicle_id", "=", self.id)])) if self.id else 0

    def _compute_maintenance_count(self):
        self.maintenance_count = len(self.env["maintenance.log"].search([("vehicle_id", "=", self.id)])) if self.id else 0

    def _compute_fuel_log_count(self):
        self.fuel_log_count = len(self.env["fuel.log"].search([("vehicle_id", "=", self.id)])) if self.id else 0

    def _compute_expense_count(self):
        self.expense_count = len(self.env["expense"].search([("vehicle_id", "=", self.id)])) if self.id else 0

    def _get_total_operational_cost(self):
        if not self.id:
            return 0.0
        maintenance_total = sum((log.cost or 0.0) for log in self.env["maintenance.log"].search([("vehicle_id", "=", self.id)]))
        fuel_total = sum((log.cost or 0.0) for log in self.env["fuel.log"].search([("vehicle_id", "=", self.id)]))
        return float(maintenance_total + fuel_total)

    def __getattr__(self, name):
        if name == "total_operational_cost":
            return self._get_total_operational_cost()
        if name == "trip_count":
            return len(self.env["trip"].search([("vehicle_id", "=", self.id)])) if self.id else 0
        if name == "maintenance_count":
            return len(self.env["maintenance.log"].search([("vehicle_id", "=", self.id)])) if self.id else 0
        if name == "fuel_log_count":
            return len(self.env["fuel.log"].search([("vehicle_id", "=", self.id)])) if self.id else 0
        if name == "expense_count":
            return len(self.env["expense"].search([("vehicle_id", "=", self.id)])) if self.id else 0
        raise AttributeError(name)

    def action_view_trips(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "trip",
            "view_mode": "list,form",
            "domain": [("vehicle_id", "=", self.id)],
            "name": f"Trips — {self.registration_number}",
        }

    def action_view_maintenance(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "maintenance.log",
            "view_mode": "list,form",
            "domain": [("vehicle_id", "=", self.id)],
            "name": f"Maintenance — {self.registration_number}",
        }

    def action_view_fuel_logs(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "fuel.log",
            "view_mode": "list,form",
            "domain": [("vehicle_id", "=", self.id)],
            "name": f"Fuel Logs — {self.registration_number}",
        }

    def action_view_expenses(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "expense",
            "view_mode": "list,form",
            "domain": [("vehicle_id", "=", self.id)],
            "name": f"Expenses — {self.registration_number}",
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
