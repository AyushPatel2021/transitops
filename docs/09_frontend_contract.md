# Frontend Contract

The frontend is intentionally generic. A normal module should not need Vue edits.

## What The Frontend Reads

From metadata endpoints:

- model description
- fields
- labels
- types
- required/readonly/invisible rules
- relation model names
- `_ui_views`
- `_search_config`
- status field
- rec name field
- permissions

From record endpoints:

- list items
- total count
- grouped results
- form record data
- domain states

From action endpoints:

- window actions
- client notifications
- file downloads
- dialog actions
- wizard actions

## What You Should Define In Backend

Backend model:

```python
_name_field_ = "name"
_status_field_ = "state"
_description_ = "Engineering Change Order"
```

Backend UI:

```python
_ui_views = {
    "list": {
        "fields": ["name", "title", "state"],
        "search_fields": ["name", "title"],
    },
    "form": {
        "groups": [...],
        "tabs": [...],
        "header_buttons": [...],
        "smart_buttons": [...],
    },
}
```

Backend search:

```python
_search_config = {
    "filters": [...],
    "group_by": [...],
}
```

Backend menu:

```python
MenuItem("plm_eco", "Engineering Changes", "/models/plm.eco", "Settings")
```

## What Not To Do

Do not add frontend `if model === "plm.eco"` conditions.

Do not hardcode:

- breadcrumbs
- button labels
- status stages
- field layout
- search filters
- menu entries
- model-specific cards
- relation dropdown behavior

If a model needs a field hidden, put `invisible` in backend metadata.

If a model needs a button, put it in `_ui_views`.

If a model needs a new list column, put it in `_ui_views["list"]["fields"]`.

If a model needs a new breadcrumb label, fix `_name_field_` or `_description_`.

## When Frontend Is Allowed

Frontend module code is allowed for:

- custom dashboards
- custom comparison pages with a defined payload
- custom report viewers
- advanced graphical editors
- highly visual planning boards

Even then, prefer a backend contract first. Example:

```python
def get_comparison_payload(self):
    return {
        "sections": [
            {"title": "Components", "rows": [...]}
        ]
    }
```

Then the frontend renders a generic comparison payload, not a PLM-only shape.

## Breadcrumbs

Breadcrumbs are managed by:

- route path
- menu label
- model description
- record display name
- action domain context

Do not add breadcrumb `if/else` conditions for modules. If breadcrumbs look wrong, fix metadata or generic breadcrumb matching.
