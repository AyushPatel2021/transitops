# Kinetic-Style Module Example

This is a practical map for building something like Kinetic PLM on top of Znova 1.

## 1. Define Roles

Add roles:

- `engineering`
- `approver`
- `operations`

Keep `admin` as full access.

Example data:

```python
"role_engineering": {
    "model": "role",
    "values": {
        "name": "engineering",
        "description": "Engineering team members",
    },
    "noupdate": True,
}
```

## 2. Define Core Models

Typical PLM models:

```text
product.product
product.version
mrp.bom
mrp.bom.line
mrp.routing.workcenter
work.center
plm.eco
plm.eco.line
plm.eco.stage
plm.eco.approval
plm.eco.workorder
```

Each model should define:

- `__tablename__`
- `_model_name_`
- `_name_field_`
- `_description_`
- fields
- relations
- `_role_permissions`
- `_ui_views`
- `_search_config` if users need filters/group-by

## 3. Define Stages

For ECO stages:

```python
class PlmEcoStage(ZnovaModel):
    __tablename__ = "plm_eco_stages"
    _model_name_ = "plm.eco.stage"
    _name_field_ = "name"

    name = fields.Char(label="Stage", required=True)
    sequence = fields.Integer(label="Sequence", default=10)
    fold = fields.Boolean(label="Folded", default=False)
```

On ECO:

```python
_status_field_ = "stage_id"

stage_id = fields.Many2one("plm.eco.stage", label="Stage", required=True)
```

The frontend status bar will load and sort stages by `sequence`.

## 4. Define ECO Form

```python
_ui_views = {
    "form": {
        "show_audit_log": True,
        "groups": [
            {
                "title": "Header",
                "fields": ["name", "title", "stage_id"],
                "position": "header",
            },
            {
                "title": "Details",
                "fields": ["product_id", "reason", "priority"],
            },
            {
                "title": "Ownership",
                "fields": ["owner_id", "effective_date"],
                "position": "right",
            },
        ],
        "tabs": [
            {"title": "Changes", "fields": ["line_ids"]},
            {"title": "Approvals", "fields": ["approval_ids"]},
            {"title": "Work Orders", "fields": ["workorder_ids"]},
        ],
        "header_buttons": [
            {
                "name": "submit",
                "label": "Submit",
                "type": "primary",
                "method": "action_submit",
                "invisible": "[('stage_id.name', '!=', 'Draft')]",
            }
        ],
        "smart_buttons": [
            {
                "name": "bom",
                "label": "BOMs",
                "icon": "Box",
                "field": "bom_count",
                "method": "action_view_boms",
            }
        ],
    },
    "list": {
        "fields": ["name", "title", "product_id", "stage_id", "owner_id"],
        "search_fields": ["name", "title", "product_id"],
    },
}
```

No frontend model-specific code is needed for this.

## 5. Define Object Actions

```python
def action_submit(self):
    self.ensure_one()
    self.write({"stage_id": self._get_stage("Submitted").id})
    return {
        "type": "ir.actions.client",
        "tag": "display_notification",
        "params": {
            "title": "Submitted",
            "message": f"{self.name} is waiting for approval.",
            "type": "success",
            "refresh": True,
        },
    }


def action_view_boms(self):
    return {
        "type": "ir.actions.act_window",
        "res_model": "mrp.bom",
        "view_mode": "list,form",
        "domain": [("product_id", "=", self.product_id)],
        "name": f"BOMs for {self.product_id.display_name}",
    }
```

## 6. Define Menus

```python
menu_manager.add_item("PLM", MenuItem(
    "plm_eco",
    "Engineering Changes",
    "/models/plm.eco",
    "Settings",
    sequence=10,
    groups=["admin", "engineering", "approver"],
))

menu_manager.add_item("PLM", MenuItem(
    "mrp_bom",
    "Bills of Materials",
    "/models/mrp.bom",
    "Box",
    sequence=20,
    groups=["admin", "engineering", "operations"],
))
```

## 7. Add Sequences

```python
"seq_plm_eco": {
    "model": "sequence",
    "values": {
        "name": "ECO Sequence",
        "code": "plm.eco",
        "prefix": "ECO-",
        "padding": 5,
        "number_next": 1,
        "active": True,
    },
    "noupdate": True,
}
```

## 8. Add Cron Jobs

Use cron for:

- approval reminders
- overdue ECO checks
- cleanup of temporary files
- scheduled notifications

Example:

```python
"cron_eco_reminders": {
    "model": "cron",
    "values": {
        "name": "ECO Approval Reminders",
        "code": "plm.eco.reminders",
        "model_name": "plm.eco",
        "function_name": "cron_send_approval_reminders",
        "interval_number": 1,
        "interval_type": "days",
        "active": True,
    },
    "noupdate": True,
}
```

## 9. Add Custom Pages Only If Needed

Generic screens handle:

- ECO list
- ECO form
- BOM list/form
- Product version list/form
- approvals
- work orders
- smart buttons
- status bar
- search/filter/group

Custom frontend page may be justified for:

- visual comparison diff
- complex report dashboard
- graphical BOM tree

Before adding a custom page, define a backend payload contract. Do not make the page depend on hardcoded PLM fields unless it is explicitly app-specific.

## 10. Test Workflow

Minimum Kinetic-style workflow tests:

1. Create product.
2. Create product version.
3. Create BOM with lines.
4. Create ECO.
5. Submit ECO.
6. Add approvals.
7. Approve/reject ECO.
8. Generate report or comparison payload if implemented.
9. Delete draft/test records.
10. Check permissions for engineering, approver, operations, and admin.

Run backend and frontend checks from [10_testing_and_verification.md](10_testing_and_verification.md).
