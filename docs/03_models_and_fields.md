# Models And Fields

Models are Python classes that inherit `ZnovaModel`.

Basic example:

```python
from backend.core.znova_model import ZnovaModel
from backend.core import fields


class ProductVersion(ZnovaModel):
    __tablename__ = "product_versions"
    _model_name_ = "product.version"
    _name_field_ = "name"
    _description_ = "Product Version"

    name = fields.Char(label="Version", required=True, tracking=True)
    description = fields.Text(label="Description")
    active = fields.Boolean(label="Active", default=True)
```

## Standard Fields

Common fields:

```python
name = fields.Char(label="Name", required=True, size=100)
description = fields.Text(label="Description")
quantity = fields.Integer(label="Quantity", default=1)
active = fields.Boolean(label="Active", default=True)
due_date = fields.Date(label="Due Date")
approved_at = fields.DateTime(label="Approved At")
metadata = fields.JSON(label="Metadata", default=dict)
state = fields.Selection([
    ("draft", "Draft"),
    ("done", "Done"),
], label="Status", default="draft")
image = fields.Image(label="Image")
attachment_id = fields.Attachment(label="Attachment")  # if available in current fields module
```

Check `backend/core/fields.py` for the exact field classes available in the current branch.

## Conditional UI Rules

`required`, `readonly`, and `invisible` can be booleans or domain strings.

```python
approval_note = fields.Text(
    label="Approval Note",
    required="[('state', '=', 'rejected')]",
    invisible="[('state', '!=', 'rejected')]",
)
```

Important: conditional `required` is a UI/runtime rule, not a database `NOT NULL`. Only `required=True` creates a database-level non-null column.

## Relations

Many2one:

```python
product_id = fields.Many2one(
    "product.product",
    label="Product",
    required=True,
    tracking=True,
)
```

One2many:

```python
line_ids = fields.One2many(
    "mrp.bom.line",
    "bom_id",
    label="Components",
    columns=["component_id", "quantity", "uom"],
)
```

Many2many:

```python
approver_ids = fields.Many2many(
    "user",
    label="Approvers",
    display_format="pills",
    searchable=True,
)
```

Use `class_name="SomeClass"` only when `_model_name_` cannot be converted to the Python class name. Normal model names should not need it.

## Methods

Use methods for business behavior:

```python
def action_submit(self):
    self.ensure_one()
    self.write({"state": "submitted"})
    return {
        "type": "ir.actions.client",
        "tag": "display_notification",
        "params": {
            "title": "Submitted",
            "message": f"{self.name} has been submitted.",
            "type": "success",
            "refresh": True,
        },
    }
```

Object methods can be called by backend-defined form buttons.

## Validation

Override `create` and `write` for validation:

```python
from sqlalchemy.orm import Session

from backend.core.exceptions import ValidationError


@classmethod
def create(cls, db: Session, vals: dict):
    if vals.get("quantity", 0) <= 0:
        raise ValidationError("Quantity must be greater than zero")
    return super().create(db, vals)


def write(self, *args, **kwargs):
    vals = args[0] if args and isinstance(args[0], dict) else kwargs.get("vals", kwargs)
    if "quantity" in vals and vals["quantity"] <= 0:
        raise ValidationError("Quantity must be greater than zero")
    return super().write(*args, **kwargs)
```

Prefer raising framework exceptions:

- `ValidationError` for invalid data.
- `UserError` for user-correctable business issues.
- `AccessError` for security failures.

## Environment Access

In model instance methods, prefer using the record environment if available:

```python
def action_view_lines(self):
    lines = self.env["mrp.bom.line"].search([("bom_id", "=", self.id)])
```

For class methods, accept an environment or use the established framework helper if present. Avoid importing and constructing infrastructure objects inside model methods unless there is no cleaner module-level option.
