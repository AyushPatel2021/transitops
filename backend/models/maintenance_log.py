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

    vehicle_id = fields.Many2one("vehicle", label="Vehicle", required=True, tracking=True)
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
    created_by = fields.Many2one("user", label="Created By", required=True, readonly=True)

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
                {"title": "Audit", "fields": ["created_by"], "position": "right"},
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
            ],
            "header_buttons": [
                {"name": "close", "label": "Close Maintenance", "type": "primary", "method": "action_close", "invisible": "[('status', '!=', 'active')]"}
            ],
        },
    }

    def action_close(self):
        if self.status != "active":
            raise UserError("Only active maintenance logs can be closed.")
        if not self.end_date:
            raise UserError("End date is required to close maintenance.")
        self.write({"status": "closed"})
        if self.vehicle and self.vehicle.status != "retired":
            self.vehicle.write({"status": "available"})
        return notify("Maintenance Closed", "Maintenance log has been closed.")
