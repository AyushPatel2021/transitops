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


class Expense(ZnovaModel):
    __tablename__ = "expenses"
    _model_name_ = "expense"
    _description_ = "Expense"

    vehicle_id = fields.Many2one("vehicle", label="Vehicle", required=True)
    expense_type = fields.Selection([("Toll", "Toll"), ("Maintenance", "Maintenance"), ("Fine", "Fine"), ("Other", "Other")], label="Expense Type", required=True)
    amount = fields.Float(label="Amount", required=True)
    date = fields.Date(label="Date", required=True, default=date.today)
    description = fields.Text(label="Description")

    _role_permissions = {
        ROLE_ADMIN: ADMIN_ALL,
        ROLE_FLEET: {"create": True, "read": True, "write": True, "delete": False, "domain": []},
        ROLE_DRIVER: NO_ACCESS,
        ROLE_SAFETY: NO_ACCESS,
        ROLE_FINANCE: ADMIN_ALL,
    }

    _ui_views = {
        "list": {"fields": ["vehicle_id", "expense_type", "amount", "date"], "search_fields": ["vehicle_id", "expense_type", "date"]},
        "form": {
            "groups": [
                {"title": "Expense", "fields": ["vehicle_id", "expense_type"], "position": "header"},
            ],
            "tabs": [
                {
                    "title": "Details",
                    "groups": [
                        {"title": "Cost", "fields": ["amount", "date"]},
                        {"title": "Description", "fields": ["description"]},
                    ],
                },
            ],
        },
    }
