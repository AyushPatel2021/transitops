# Actions, Services, And Custom Routes

Most user actions should be model methods exposed through generic object buttons.

## Window Actions

Open another model list or form:

```python
def action_view_lines(self):
    return {
        "type": "ir.actions.act_window",
        "res_model": "mrp.bom.line",
        "view_mode": "list,form",
        "domain": [("bom_id", "=", self.id)],
        "name": f"Components of {self.name}",
    }
```

The frontend navigates to the generic model screen and keeps breadcrumb context.

## Client Notifications

```python
return {
    "type": "ir.actions.client",
    "tag": "display_notification",
    "params": {
        "title": "Approved",
        "message": f"{self.name} has been approved.",
        "type": "success",
        "refresh": True,
    },
}
```

## Download File

If a backend action generates a file URL:

```python
return {
    "type": "ir.actions.client",
    "tag": "download_file",
    "params": {
        "url": f"/models/{self._model_name_}/{self.id}/report_pdf",
        "filename": f"{self.name}.pdf",
    },
}
```

The frontend downloads the blob generically.

## Dialog Actions

The generic view supports backend dialog actions:

```python
return {
    "type": "ir.actions.dialog",
    "dialog_type": "confirm",
    "title": "Confirm Approval",
    "message": "Approve this record?",
    "severity": "warning",
    "on_confirm": {
        "method": "action_approve_confirmed",
    },
}
```

## Custom Comparison And PDF Hooks

Generic endpoints exist for models that implement methods:

```python
def get_comparison_payload(self):
    return {
        "title": self.name,
        "sections": [],
    }


def generate_report_pdf(self):
    return bytes_data
```

Endpoints:

```text
GET /api/v1/models/{model}/{id}/comparison
GET /api/v1/models/{model}/{id}/report_pdf
```

If the payload is very module-specific, keep the custom page outside the framework or define a generic payload contract first.

## Services

Use `backend/services` for reusable business logic that does not belong directly on one model.

Example:

```python
class EcoReportService:
    def build_payload(self, eco):
        return {
            "name": eco.name,
            "lines": [line.to_dict() for line in eco.line_ids],
        }
```

Services should not know about Vue. Return Python data or bytes.

## Custom API Routes

Only add custom routes for behavior that cannot be expressed through:

- generic CRUD
- object method call
- window action
- client action
- comparison hook
- report hook

Custom endpoint file:

```python
from fastapi import APIRouter

router = APIRouter()


@router.get("/plm/special-summary")
def special_summary():
    return {"items": []}
```

Then include the router in the application startup/router registration, following existing endpoint patterns.

Do not add custom routes for ordinary model list, form, create, write, delete, or button calls.
