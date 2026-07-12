# Module Anatomy

Znova 1 does not currently have isolated addon folders like Odoo. A business module is made by adding files to the existing backend packages.

For a module like Kinetic PLM, the files usually look like this:

```text
backend/models/
  product_template.py
  product_product.py
  product_version.py
  mrp_bom.py
  mrp_bom_line.py
  plm_eco.py
  plm_eco_line.py
  plm_eco_stage.py

backend/services/
  eco_report_service.py
  approval_reminder_service.py

backend/data/
  kinetic_init_data.py
  kinetic_menus.py
  kinetic_sequences.py
  kinetic_crons.py

backend/demo/
  kinetic_demo_data.py

backend/api/v1/endpoints/
  kinetic_custom_api.py

backend/tests/
  test_kinetic_models.py
  test_kinetic_workflows.py
```

You do not need all of these for every module.

## Minimum Module

A minimum module needs:

1. One or more model files in `backend/models`.
2. Menu entries in `backend/data/menus.py` or a module-specific menu initializer called from there.
3. Role permissions on every model.
4. `_ui_views` on every model you want users to open.
5. Tests for create/read/write/delete and key actions.

## Model Discovery

`backend/models/__init__.py` recursively imports modules under `backend/models`. In practice this means a new model file is discovered automatically when the backend imports `backend.models`.

Even though discovery is automatic, keep model files importable. Avoid side effects at import time except model declarations.

## Package Exports

For new Python packages, always add `__init__.py`. For existing packages, keep imports clean and top-level.

Project import rules:

- one import per line
- imports at top of file
- no local imports inside functions
- standard library first
- third-party next
- internal framework imports next
- app model/service imports last

## Naming

Use three names deliberately:

```python
class MrpBom(ZnovaModel):
    __tablename__ = "mrp_bom"
    _model_name_ = "mrp.bom"
    _name_field_ = "name"
    _description_ = "Bill of Materials"
```

- `__tablename__`: physical database table.
- `_model_name_`: framework/API model identifier.
- `_name_field_`: display label for breadcrumbs, Many2one labels, and titles.
- `_description_`: human label used in metadata and UI.

Do not remove these just because they look similar. They serve different layers.
