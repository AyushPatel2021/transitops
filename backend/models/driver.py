from datetime import date
from datetime import timedelta

from backend.core import fields
from backend.core.base_model import Environment
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


class Driver(ZnovaModel):
    __tablename__ = "drivers"
    _model_name_ = "driver"
    _name_field_ = "name"
    _status_field_ = "status"
    _description_ = "Driver"

    user_id = fields.Many2one("user", label="User", unique=True, ondelete="set null")
    name = fields.Char(label="Name", required=True, size=120, tracking=True)
    license_number = fields.Char(label="License Number", required=True, unique=True, size=80, tracking=True)
    license_category = fields.Selection(
        [("LMV", "LMV"), ("HMV", "HMV"), ("Heavy Truck", "Heavy Truck"), ("Trailer", "Trailer")],
        label="License Category",
        required=True,
        tracking=True,
    )
    license_expiry_date = fields.Date(label="License Expiry Date", required=True, tracking=True)
    license_valid = fields.Boolean(label="License Valid", compute="_compute_license_valid", store=False, readonly=True)
    contact_number = fields.Char(label="Contact Number", required=True, size=40, tracking=True)
    safety_score = fields.Float(label="Safety Score", default=100, tracking=True)
    status = fields.Selection(
        [("available", "Available"), ("on_trip", "On Trip"), ("off_duty", "Off Duty"), ("suspended", "Suspended")],
        label="Status",
        required=True,
        default="available",
        readonly=True,
        tracking=True,
    )
    region_id = fields.Many2one("region", label="Region", domain="[('active', '=', True)]")
    trip_count = fields.Integer(label="Trip Count", compute="_compute_trip_count", store=False, readonly=True)
    attachments = fields.Attachments(
        label="Attachments",
        max_files=12,
        allowed_types=["pdf", "jpg", "jpeg", "png", "doc", "docx"],
        help="Driver license, compliance, and identity documents",
    )

    def _compute_license_valid(self):
        self.license_valid = bool(self.license_expiry_date and self.license_expiry_date >= date.today())

    def _compute_trip_count(self):
        self.trip_count = len(self.env["trip"].search([("driver_id", "=", self.id)])) if self.id else 0

    def __getattr__(self, name):
        if name == "license_valid":
            return bool(self.license_expiry_date and self.license_expiry_date >= date.today())
        if name == "trip_count":
            return len(self.env["trip"].search([("driver_id", "=", self.id)])) if self.id else 0
        raise AttributeError(name)

    def action_view_trips(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "trip",
            "view_mode": "list,form",
            "domain": [("driver_id", "=", self.id)],
            "name": f"Trips — {self.name}",
        }

    _role_permissions = {
        ROLE_ADMIN: ADMIN_ALL,
        ROLE_FLEET: {"create": True, "read": True, "write": True, "delete": False, "domain": []},
        ROLE_DRIVER: READ_ALL,
        ROLE_SAFETY: ADMIN_ALL,
        ROLE_FINANCE: READ_ALL,
    }

    _ui_views = {
        "list": {
            "fields": ["name", "license_number", "license_category", "license_expiry_date", "license_valid", "safety_score", "status", "region_id"],
            "search_fields": ["name", "license_number", "status", "region_id"],
        },
        "form": {
            "show_audit_log": True,
            "groups": [
                {"title": "Driver", "fields": ["name"], "position": "header"},
            ],
            "tabs": [
                {
                    "title": "Profile",
                    "groups": [
                        {"title": "Contact", "fields": ["user_id", "contact_number", "region_id"]},
                    ],
                },
                {
                    "title": "Compliance",
                    "groups": [
                        {"title": "License", "fields": ["license_number", "license_category", "license_expiry_date", "license_valid"]},
                        {"title": "Safety", "fields": ["safety_score"]},
                    ],
                },
                {
                    "title": "Attachments",
                    "groups": [
                        {"title": "Documents", "fields": ["attachments"]},
                    ],
                },
            ],
            "header_buttons": [
                {"name": "suspend", "label": "Suspend", "type": "secondary", "method": "action_suspend", "invisible": "[('status', '=', 'suspended')]"},
                {"name": "reinstate", "label": "Reinstate", "type": "primary", "method": "action_reinstate", "invisible": "[('status', '!=', 'suspended')]"},
            ],
            "smart_buttons": [
                {
                    "name": "trips",
                    "label": "Trips",
                    "icon": "Route",
                    "field": "trip_count",
                    "method": "action_view_trips",
                    "groups": ["admin", "fleet_manager", "safety_officer"],
                },
            ],
        },
    }

    _search_config = {
        "filters": [
            {"name": "available", "label": "Available", "domain": "[('status', '=', 'available')]"},
            {"name": "on_trip", "label": "On Trip", "domain": "[('status', '=', 'on_trip')]"},
            {"name": "suspended", "label": "Suspended", "domain": "[('status', '=', 'suspended')]"},
            {"name": "off_duty", "label": "Off Duty", "domain": "[('status', '=', 'off_duty')]"},
            {"name": "expiring_license", "label": "License Expiring (30 days)", "domain": "[('license_expiry_date', '<=', (date.today() + timedelta(days=30)).isoformat()), ('license_expiry_date', '>=', date.today().isoformat())]"},
            {"name": "expired_license", "label": "License Expired", "domain": "[('license_expiry_date', '<', date.today().isoformat())]"},
            {"name": "lmv", "label": "LMV", "domain": "[('license_category', '=', 'LMV')]"},
            {"name": "hmv", "label": "HMV", "domain": "[('license_category', '=', 'HMV')]"},
        ],
        "group_by": [
            {"name": "by_status", "label": "By Status", "field": "status"},
            {"name": "by_license_category", "label": "By License Category", "field": "license_category"},
            {"name": "by_region", "label": "By Region", "field": "region_id"},
        ],
    }

    def _assert_safety_role(self):
        role = get_action_role_name(self)
        if role not in (ROLE_ADMIN, ROLE_SAFETY):
            raise UserError("Only Safety Officer or Admin can update driver compliance status.")

    def action_suspend(self):
        self._assert_safety_role()
        self.write({"status": "suspended"})
        return notify("Driver Suspended", f"{self.name} is now suspended.")

    def action_reinstate(self):
        self._assert_safety_role()
        self.write({"status": "available"})
        return notify("Driver Reinstated", f"{self.name} is now available.")

    @classmethod
    def send_license_expiry_reminders(cls, db):
        env = Environment(db)
        today = date.today()
        reminder_limit = today + timedelta(days=30)
        drivers = env["driver"].search([
            ("license_expiry_date", ">=", today),
            ("license_expiry_date", "<=", reminder_limit),
        ])

        role = env["role"].search([("name", "=", ROLE_SAFETY)], limit=1)
        if not role:
            return {
                "checked": len(drivers),
                "sent": 0,
                "skipped": len(drivers),
                "failed": 0,
                "reason": "Safety Officer role not found",
            }

        safety_users = env["user"].search([
            ("role_id", "=", role.id),
            ("is_active", "=", True),
        ])
        user_ids = safety_users.ids()
        if not user_ids:
            return {
                "checked": len(drivers),
                "sent": 0,
                "skipped": len(drivers),
                "failed": 0,
                "reason": "No active Safety Officer users found",
            }

        from backend.services.notification_service import get_notification_service

        notification_service = get_notification_service(db)
        sent = 0
        skipped = 0
        failed = 0
        for driver in drivers:
            days_left = (driver.license_expiry_date - today).days
            message = (
                f"Driver {driver.name}'s license expires in {days_left} day"
                f"{'s' if days_left != 1 else ''} ({driver.license_expiry_date.isoformat()})."
            )

            try:
                notifications = notification_service.notify_users(
                    user_ids=user_ids,
                    title="Driver license expiring soon",
                    message=message,
                    notification_type="warning",
                    action={
                        "type": "navigate",
                        "target": f"/models/driver/{driver.id}",
                    },
                )
                sent += len(notifications)
            except Exception:
                failed += 1

        return {
            "checked": len(drivers),
            "sent": sent,
            "skipped": skipped,
            "failed": failed,
        }

    def unlink(self, *args, **kwargs):
        trips = self.env["trip"].search([("driver_id", "=", self.id)], limit=1)
        if trips:
            raise UserError("Cannot delete a driver with trip history. Set the driver off duty or suspended instead.")
        return super().unlink(*args, **kwargs)
