# UI Metadata

The frontend renders model screens from `_ui_views` and `_search_config`.

## List View

```python
_ui_views = {
    "list": {
        "fields": ["name", "product_id", "state", "updated_at"],
        "search_fields": ["name", "product_id", "state"],
    }
}
```

List view supports:

- visible columns
- search fields
- pagination
- filters from `_search_config`
- group-by from `_search_config`
- bulk delete when permissions allow it

## Form View

```python
_ui_views = {
    "form": {
        "show_audit_log": True,
        "groups": [
            {
                "title": "Header",
                "fields": ["name", "state"],
                "position": "header",
            },
            {
                "title": "Main Information",
                "fields": ["product_id", "description"],
            },
            {
                "title": "Sidebar",
                "fields": ["owner_id", "created_at"],
                "position": "right",
            },
        ],
    }
}
```

Supported group positions:

- default body group
- `header`
- `right`

## Tabs

```python
"tabs": [
    {
        "title": "Components",
        "fields": ["line_ids"],
    },
    {
        "title": "Approval",
        "fields": ["approval_ids"],
        "invisible": "[('state', '=', 'draft')]",
    },
]
```

Tabs can be hidden by backend domain expressions. The frontend automatically switches away from a tab when it becomes invisible.

## Header Buttons

```python
"header_buttons": [
    {
        "name": "submit",
        "label": "Submit",
        "type": "primary",
        "method": "action_submit",
        "invisible": "[('state', '!=', 'draft')]",
    }
]
```

The frontend calls:

```text
POST /api/v1/models/{model}/{id}/call/{method}
```

The method should return an action dict or `None`.

## Smart Buttons

```python
"smart_buttons": [
    {
        "name": "bom_lines",
        "label": "Components",
        "icon": "Box",
        "field": "line_count",
        "method": "action_view_lines",
    }
]
```

If `field` is empty, `0`, `None`, `False`, or an empty list, the smart button is hidden automatically.

## Status Bar

Declare the status field on the model:

```python
_status_field_ = "state"

state = fields.Selection([
    ("draft", "Draft"),
    ("submitted", "Submitted"),
    ("approved", "Approved"),
], default="draft")
```

Many2one status fields are also supported:

```python
_status_field_ = "stage_id"

stage_id = fields.Many2one("plm.eco.stage", label="Stage")
```

The frontend loads relation records and sorts by `sequence` if present.

## Search Config

```python
_search_config = {
    "filters": [
        {
            "name": "active",
            "label": "Active",
            "domain": "[('active', '=', True)]",
            "default": True,
        },
        {
            "name": "draft",
            "label": "Draft",
            "domain": "[('state', '=', 'draft')]",
        },
    ],
    "group_by": [
        {
            "name": "by_state",
            "label": "By State",
            "field": "state",
        },
        {
            "name": "by_owner",
            "label": "By Owner",
            "field": "owner_id",
        },
    ],
}
```

Default filters are applied by `GenericView` when there are no filters in the URL.

## Attachments

Readonly attachment fields still render as attachment widgets. Do not convert attachments to plain text in module-specific code.
