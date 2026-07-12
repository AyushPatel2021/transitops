ROLE_ADMIN = "admin"
ROLE_FLEET = "fleet_manager"
ROLE_DRIVER = "driver"
ROLE_SAFETY = "safety_officer"
ROLE_FINANCE = "financial_analyst"

ALL_ROLES = [ROLE_ADMIN, ROLE_FLEET, ROLE_DRIVER, ROLE_SAFETY, ROLE_FINANCE]
READ_ALL = {"create": False, "read": True, "write": False, "delete": False, "domain": []}
NO_ACCESS = {"create": False, "read": False, "write": False, "delete": False, "domain": []}
ADMIN_ALL = {"create": True, "read": True, "write": True, "delete": True, "domain": []}


def get_action_user(record):
    action_user_id = getattr(record, "_action_user_id", None) or getattr(record, "_audit_user_id", None)
    if action_user_id:
        from sqlalchemy.orm import object_session
        from backend.core.registry import registry

        db = object_session(record)
        user_model = registry.get_model("user")
        if db and user_model:
            return db.query(user_model).filter(user_model.id == action_user_id).first()

    env = getattr(record, "env", None)
    return env.user if env else None


def get_action_role_name(record):
    user = get_action_user(record)
    return user.role.name if user and user.role else None


def notify(title, message, level="success"):
    return {
        "type": "ir.actions.client",
        "tag": "display_notification",
        "params": {
            "title": title,
            "message": message,
            "type": level,
            "refresh": True,
        },
    }
