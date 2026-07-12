from backend.core import fields
from backend.core.exceptions import UserError
from backend.core.znova_model import ZnovaModel
from backend.models.transitops_common import ADMIN_ALL
from backend.models.transitops_common import NO_ACCESS
from backend.models.transitops_common import READ_ALL
from backend.models.transitops_common import ROLE_ADMIN
from backend.models.transitops_common import ROLE_DRIVER
from backend.models.transitops_common import ROLE_FINANCE
from backend.models.transitops_common import ROLE_FLEET
from backend.models.transitops_common import ROLE_SAFETY
from backend.models.transitops_common import notify


class MaintenanceLog(ZnovaModel):
    __tablename__ = "maintenance_logs"
    _model_name_ = "maintenance.log"
    _name_field_ = "maintenance_type"
    _status_field_ = "status"
    _description_ = "Maintenance Log"

    vehicle_id = fields.Many2one("vehicle", label="Vehicle", required=True, domain="[('status', '=', 'available')]", tracking=True)
    maintenance_type = fields.Selection(
        [("Oil Change", "Oil Change"), ("Tyre", "Tyre"), ("Brake", "Brake"), ("Engine", "Engine"), ("Body", "Body"), ("Other", "Other")],
        label="Maintenance Type",
        required=True,
    )
    description = fields.Text(label="Description")
    cost = fields.Float(label="Cost", required=True)
    start_date = fields.Date(label="Start Date", required=True)
    end_date = fields.Date(label="End Date")
    status = fields.Selection([("active", "Active"), ("closed", "Closed")], label="Status", required=True, default="active", readonly=True)
    created_by = fields.Many2one("user", label="Created By", readonly=True)

    _role_permissions = {
        ROLE_ADMIN: ADMIN_ALL,
        ROLE_FLEET: ADMIN_ALL,
        ROLE_DRIVER: NO_ACCESS,
        ROLE_SAFETY: NO_ACCESS,
        ROLE_FINANCE: READ_ALL,
    }

    _ui_views = {
        "list": {
            "fields": ["vehicle_id", "maintenance_type", "cost", "start_date", "end_date", "status"],
            "search_fields": ["vehicle_id", "maintenance_type", "status"],
        },
        "form": {
            "groups": [
                {"title": "Maintenance", "fields": ["vehicle_id"], "position": "header"},
            ],
            "tabs": [
                {
                    "title": "Work",
                    "groups": [
                        {"title": "Type", "fields": ["maintenance_type"]},
                        {"title": "Schedule", "fields": ["start_date", "end_date"]},
                        {"title": "Details", "fields": ["description"]},
                    ],
                },
                {
                    "title": "Cost",
                    "groups": [
                        {"title": "Cost", "fields": ["cost"]},
                    ],
                },
                {
                    "title": "Audit",
                    "groups": [
                        {"title": "Audit", "fields": ["created_by"]},
                    ],
                },
            ],
            "header_buttons": [
                {"name": "close", "label": "Close Maintenance", "type": "primary", "method": "action_close", "invisible": "[('status', '!=', 'active')]"}
            ],
        },
    }

    @classmethod
    def create(cls, db, vals, **kwargs):
        vals = vals.copy()
        user_id = kwargs.get("user_id")
        if user_id and not vals.get("created_by"):
            vals["created_by"] = user_id

        cls._validate_create_values(db, vals)
        record = super().create(db, vals, **kwargs)
        if record.status == "active" and record.vehicle and record.vehicle.status != "retired":
            record.vehicle.write({"status": "in_shop"})
        return record

    @classmethod
    def _validate_create_values(cls, db, vals):
        vehicle_id = vals.get("vehicle_id")
        if isinstance(vehicle_id, dict):
            vehicle_id = vehicle_id.get("id")
        if not vehicle_id:
            return

        from backend.core.base_model import Environment

        env = Environment(db)

        if vals.get("status", "active") == "active":
            existing = env["maintenance.log"].search([("vehicle_id", "=", vehicle_id), ("status", "=", "active")], limit=1)
            if existing:
                raise UserError("A vehicle can only have one active maintenance log at a time.")

        vehicle = env["vehicle"].browse(vehicle_id)
        if vehicle and vehicle.status != "available":
            raise UserError("Maintenance can only be started for an available vehicle.")

    def write(self, *args, **kwargs):
        vals = args[1] if len(args) == 2 else args[0] if args else kwargs.get("vals", {})
        # Block status changes only when the incoming value differs from the
        # current one AND the transition wasn't triggered by action_close.
        # This allows normal field saves (end_date, description, cost, etc.)
        # that happen to include the unchanged status in the payload.
        if (
            "status" in vals
            and vals["status"] != self.status
            and not getattr(self, "_allow_status_transition", False)
        ):
            raise UserError("Maintenance status can only be changed through Close Maintenance.")
        return super().write(*args, **kwargs)

    def action_close(self):
        if self.status != "active":
            raise UserError("Only active maintenance logs can be closed.")
        if not self.end_date:
            raise UserError("End date is required to close maintenance.")
        self._allow_status_transition = True
        try:
            self.write({"status": "closed"})
        finally:
            self._allow_status_transition = False
        if self.vehicle and self.vehicle.status != "retired":
            self.vehicle.write({"status": "available"})
        return notify("Maintenance Closed", "Maintenance log has been closed.")
