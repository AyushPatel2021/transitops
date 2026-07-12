# Sequences And Cron Jobs

## Sequences

Use sequences when records need automatic numbers like:

- ECO-00001
- BOM-00001
- PV-00001

Model example:

```python
from backend.core.sequence_mixin import SequenceMixin
from backend.core.znova_model import ZnovaModel
from backend.core import fields


class PlmEco(SequenceMixin, ZnovaModel):
    __tablename__ = "plm_eco"
    _model_name_ = "plm.eco"
    _name_field_ = "name"

    _sequence_field = "name"
    _sequence_code = "plm.eco"

    name = fields.Char(label="ECO Number", default="New", readonly=True)
    title = fields.Char(label="Title", required=True)
```

Create sequence data:

```python
"seq_plm_eco": {
    "model": "sequence",
    "values": {
        "name": "Engineering Change Order",
        "code": "plm.eco",
        "prefix": "ECO-",
        "padding": 5,
        "number_next": 1,
        "active": True,
    },
    "noupdate": True,
}
```

When the frontend creates a record with `"New"` or an empty value in the sequence field, the backend generates the next number.

## Cron Jobs

Cron jobs are records in model `cron`.

Cron data example:

```python
"cron_approval_reminders": {
    "model": "cron",
    "values": {
        "name": "Send ECO Approval Reminders",
        "code": "plm.eco.approval.reminders",
        "model_name": "plm.eco",
        "function_name": "cron_send_approval_reminders",
        "interval_number": 1,
        "interval_type": "days",
        "priority": 5,
        "active": True,
    },
    "noupdate": True,
}
```

Model method:

```python
@classmethod
def cron_send_approval_reminders(cls, db):
    env = cls.env_for()
    pending = env["plm.eco"].search([("state", "=", "waiting_approval")])
    for eco in pending:
        eco.send_approval_reminder()
```

Match the method signature to how the cron executor calls it in `backend/models/cron.py`.

## Automatic Scheduler

The background scheduler periodically checks database cron records and runs due jobs. Once cron records exist and the app is running, module cron jobs should not require a separate frontend or manual route.

## Cron Safety

Cron methods should be:

- idempotent where possible
- safe to retry
- narrow in scope
- logged clearly
- protected by business rules

Do not put long blocking work directly in request handlers if a cron/service workflow is better.
