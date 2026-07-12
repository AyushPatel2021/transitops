"""
Audit Log Model - Tracks field changes across all models
"""

from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from backend.core.znova_model import ZnovaModel
from backend.core import fields as field_types


class AuditLog(ZnovaModel):
    """
    Model to track field changes for auditing purposes.
    Records who changed what field, when, and from what value to what value.
    """
    __tablename__ = "audit_log"
    _model_name_ = "audit.log"
    _description_ = "Audit Log"
    
    # Core fields
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # What was changed
    res_model = field_types.Char(
        label="Model Name",
        required=True,
        help="The model name where the change occurred"
    )
    res_id = field_types.Integer(
        label="Record ID",
        required=True,
        help="The ID of the record that was changed"
    )
    field_name = field_types.Char(
        label="Field Name",
        required=False,  # Not required for grouped changes
        help="The name of the field that was changed (or comma-separated for multiple fields)"
    )
    field_label = field_types.Char(
        label="Field Label",
        help="The human-readable label of the field (or comma-separated for multiple fields)"
    )
    
    # Change details - now supports JSON for multiple fields
    old_value = field_types.Text(
        label="Old Value",
        help="The value before the change (or JSON for multiple fields)"
    )
    new_value = field_types.Text(
        label="New Value",
        help="The value after the change (or JSON for multiple fields)"
    )
    
    # New field to store structured changes for multiple fields
    changes_json = field_types.Text(
        label="Changes JSON",
        help="JSON structure containing multiple field changes"
    )
    
    # Who and when
    user_id = field_types.Many2one(
        "user",
        label="Changed By",
        required=True,
        help="The user who made the change"
    )
    changed_at = field_types.DateTime(
        label="Changed At",
        required=True,
        default=func.now(),
        help="When the change was made"
    )
    
    # Change type
    change_type = field_types.Selection(
        selection=[
            ('create', 'Created'),
            ('write', 'Updated'),
            ('delete', 'Deleted')
        ],
        label="Change Type",
        required=True,
        default='write'
    )
    
    _ui_views = {
        "tree": {
            "fields": ["field_label", "old_value", "new_value", "user_id", "changed_at", "change_type"]
        },
        "form": {
            "header": [],
            "groups": [
                {
                    "title": "Change Details",
                    "fields": ["res_model", "res_id", "field_name", "field_label", "change_type"]
                },
                {
                    "title": "Values",
                    "fields": ["old_value", "new_value"]
                },
                {
                    "title": "Metadata",
                    "fields": ["user_id", "changed_at"]
                }
            ]
        }
    }
