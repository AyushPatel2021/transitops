# Security, Roles, And Permissions

Every business model should define `_role_permissions`.

Example:

```python
_role_permissions = {
    "admin": {
        "create": True,
        "read": True,
        "write": True,
        "delete": True,
        "domain": [],
    },
    "engineering": {
        "create": True,
        "read": True,
        "write": True,
        "delete": False,
        "domain": [],
    },
    "approver": {
        "create": False,
        "read": True,
        "write": True,
        "delete": False,
        "domain": [("approver_ids", "in", "user.id")],
    },
    "user": {
        "create": False,
        "read": True,
        "write": False,
        "delete": False,
        "domain": [],
    },
}
```

The frontend uses permission endpoints to decide whether to show create/save/delete buttons and whether fields should become readonly.

## Role Records

Base roles live in `backend/data/init_data.py`.

Default roles:

- `admin`
- `user`

If a module needs more roles, add records:

```python
"role_engineering": {
    "model": "role",
    "values": {
        "name": "engineering",
        "description": "Engineering users who manage product design data",
    },
    "noupdate": True,
}
```

Then reference that role name in `_role_permissions`.

## Domain Rules

Domains restrict visible records for a role.

Examples:

```python
("owner_id", "=", "user.id")
("company_id", "=", "user.company_id")
("state", "in", ["submitted", "approved"])
```

Keep domain rules backend-owned. Do not filter security-sensitive data only in frontend code.

## Model Permissions vs Role Model JSON

There are two permission concepts:

1. `_role_permissions` on models: direct model-level permissions used by the framework.
2. `Role.permissions` / `Role.domain_rules`: configurable JSON on role records.

For module development, start with `_role_permissions`. Only use role JSON if you need runtime-editable permissions.

## UI Permissions

The frontend permission layer expects generic endpoints to answer:

- can create?
- can read?
- can write?
- can delete?

Based on that, the generic UI:

- hides New when create is false
- hides Save when write/create is false
- hides Delete when delete is false
- makes form fields readonly when write is false

Do not implement per-module permission UI in Vue.
