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


class Expense(ZnovaModel):
    __tablename__ = "expenses"
    _model_name_ = "expense"
    _name_field_ = "rec_name"
    _description_ = "Expense"

    vehicle_id = fields.Many2one("vehicle", label="Vehicle", required=True)
    expense_type = fields.Selection([("Toll", "Toll"), ("Maintenance", "Maintenance"), ("Fine", "Fine"), ("Other", "Other")], label="Expense Type", required=True)
    amount = fields.Float(label="Amount", required=True)
    date = fields.Date(label="Date", required=True, default=date.today)
    description = fields.Text(label="Description")
    rec_name = fields.Char(label="Reference", compute="_compute_rec_name", store=False, readonly=True)

    def _compute_rec_name(self):
        vehicle = getattr(self, "vehicle", None)
        reg = getattr(vehicle, "registration_number", None) if vehicle else None
        expense_type = self.expense_type or ""
        date_str = str(self.date) if self.date else ""
        parts = [p for p in [reg, expense_type, date_str] if p]
        self.rec_name = " / ".join(parts) if parts else f"Expense #{self.id or 'New'}"

    def __getattr__(self, name):
        if name == "rec_name":
            vehicle = object.__getattribute__(self, "__dict__").get("vehicle") or getattr(self, "vehicle", None)
            reg = getattr(vehicle, "registration_number", None) if vehicle else None
            try:
                expense_type = object.__getattribute__(self, "expense_type") or ""
            except AttributeError:
                expense_type = ""
            try:
                date_val = object.__getattribute__(self, "date")
            except AttributeError:
                date_val = None
            date_str = str(date_val) if date_val else ""
            parts = [p for p in [reg, expense_type, date_str] if p]
            return " / ".join(parts) if parts else f"Expense #{getattr(self, 'id', 'New')}"
        raise AttributeError(name)

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

    _search_config = {
        "filters": [
            {"name": "toll", "label": "Toll", "domain": "[('expense_type', '=', 'Toll')]"},
            {"name": "fine", "label": "Fine", "domain": "[('expense_type', '=', 'Fine')]"},
            {"name": "maintenance", "label": "Maintenance", "domain": "[('expense_type', '=', 'Maintenance')]"},
            {"name": "other", "label": "Other", "domain": "[('expense_type', '=', 'Other')]"},
        ],
        "group_by": [
            {"name": "by_type", "label": "By Type", "field": "expense_type"},
            {"name": "by_vehicle", "label": "By Vehicle", "field": "vehicle_id"},
        ],
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
        if "amount" in vals and vals["amount"] is not None and float(vals["amount"]) < 0:
            raise UserError("Expense amount cannot be negative.")
