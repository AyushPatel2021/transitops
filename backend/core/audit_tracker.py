"""
Audit Tracker - Helper functions for tracking field changes
"""

import logging
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from datetime import datetime, date

logger = logging.getLogger(__name__)


def format_value_for_audit(value: Any, field_type: str, field_meta: Dict = None) -> str:
    """
    Format a field value for storage in audit log.
    Converts complex types to human-readable strings.
    """
    if value is None:
        return ""
    
    # Handle relational fields
    if field_type == "many2one":
        if isinstance(value, dict) and 'display_name' in value:
            return value['display_name']
        elif isinstance(value, dict) and 'name' in value:
            return value['name']
        elif hasattr(value, 'display_name'):
            return value.display_name
        elif hasattr(value, 'name'):
            return value.name
        else:
            return str(value)
    
    elif field_type in ("one2many", "many2many"):
        # For relational lists, show count
        if isinstance(value, list):
            return f"{len(value)} record(s)"
        return str(value)
    
    elif field_type == "boolean":
        return "Yes" if value else "No"
    
    elif field_type == "selection":
        # Try to get the label from selection options
        if field_meta and 'selection' in field_meta:
            selection = field_meta['selection']
            if isinstance(selection, list):
                for option in selection:
                    if isinstance(option, (list, tuple)) and len(option) >= 2:
                        if option[0] == value:
                            return option[1]
            elif isinstance(selection, dict):
                return selection.get(value, str(value))
        return str(value)
    
    elif field_type in ("date", "datetime"):
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d %H:%M:%S") if field_type == "datetime" else value.strftime("%Y-%m-%d")
        return str(value)
    
    # Default: convert to string
    return str(value)


def should_track_field(field_name: str, field_meta: Dict) -> bool:
    """
    Determine if a field should be tracked based on its metadata.
    """
    # Don't track system fields
    if field_name in ('id', 'created_at', 'updated_at'):
        return False
    
    # Check if tracking is explicitly enabled
    return field_meta.get('tracking', False)


def get_tracked_fields(model_class) -> Dict[str, Dict]:
    """
    Get all fields that have tracking enabled for a model.
    Returns dict of {field_name: field_metadata}
    """
    tracked_fields = {}
    
    if hasattr(model_class, '_ui_metadata'):
        for field_name, field_meta in model_class._ui_metadata.items():
            if should_track_field(field_name, field_meta):
                tracked_fields[field_name] = field_meta
    
    return tracked_fields


def create_audit_log_entry(
    db: Session,
    model_name: str,
    record_id: int,
    field_name: str,
    field_label: str,
    old_value: Any,
    new_value: Any,
    user_id: int,
    change_type: str = 'write',
    field_type: str = None,
    field_meta: Dict = None,
    values_already_formatted: bool = False
):
    """
    Create an audit log entry for a field change.
    
    Args:
        values_already_formatted: If True, old_value and new_value are already
                                 formatted strings and won't be formatted again.
    """
    try:
        from backend.models.audit_log import AuditLog
        
        # Format values for display (unless already formatted)
        if values_already_formatted:
            old_value_str = old_value if isinstance(old_value, str) else str(old_value)
            new_value_str = new_value if isinstance(new_value, str) else str(new_value)
        else:
            old_value_str = format_value_for_audit(old_value, field_type, field_meta)
            new_value_str = format_value_for_audit(new_value, field_type, field_meta)
        
        # Only create log if values actually changed
        if old_value_str == new_value_str and change_type == 'write':
            return
        
        audit_entry = AuditLog(
            res_model=model_name,
            res_id=record_id,
            field_name=field_name,
            field_label=field_label,
            old_value=old_value_str,
            new_value=new_value_str,
            user_id=user_id,
            changed_at=datetime.utcnow(),
            change_type=change_type
        )
        
        db.add(audit_entry)
        # Don't commit here - let the parent transaction handle it
        
        logger.info(f"[AUDIT] Created audit log entry: {model_name}:{record_id} - {field_name}: {old_value_str} -> {new_value_str}")
        
    except Exception as e:
        logger.error(f"[AUDIT] Failed to create audit log entry: {e}")
        import traceback
        logger.error(f"[AUDIT] Traceback: {traceback.format_exc()}")
        # Don't raise - audit logging should not break the main operation


def track_record_creation(
    db: Session,
    model_class,
    record,
    user_id: int
):
    """
    Track the creation of a new record.
    Creates a single audit log entry indicating the record was created.
    """
    try:
        from backend.models.audit_log import AuditLog
        
        model_name = getattr(model_class, '_model_name_', model_class.__name__)
        
        # Create a "Record Created" entry
        audit_entry = AuditLog(
            res_model=model_name,
            res_id=record.id,
            field_name='__record__',
            field_label='Record',
            old_value='',
            new_value='Created',
            user_id=user_id,
            changed_at=datetime.utcnow(),
            change_type='create'
        )
        
        db.add(audit_entry)
        logger.debug(f"Tracked record creation: {model_name}:{record.id}")
        
    except Exception as e:
        logger.error(f"Failed to track record creation: {e}")


def track_field_changes(
    db: Session,
    model_class,
    record,
    old_values: Dict[str, Any],
    new_values: Dict[str, Any],
    user_id: int
):
    """
    Track changes to tracked fields.
    Groups all changes in a single transaction into one audit log entry.
    """
    try:
        from backend.models.audit_log import AuditLog
        import json
        
        tracked_fields = get_tracked_fields(model_class)
        
        if not tracked_fields:
            return  # No fields to track
        
        model_name = getattr(model_class, '_model_name_', model_class.__name__)
        
        logger.info(f"[AUDIT] Tracking changes for {model_name}:{record.id}")
        logger.info(f"[AUDIT] Tracked fields: {list(tracked_fields.keys())}")
        logger.info(f"[AUDIT] New values keys: {list(new_values.keys())}")
        
        # Collect all changes
        changes = []
        
        for field_name, field_meta in tracked_fields.items():
            # Check if this field was changed
            if field_name in new_values:
                old_value = old_values.get(field_name)
                new_value = new_values.get(field_name)
                
                # Get field type for proper formatting
                field_type = field_meta.get('type', 'char')
                field_label = field_meta.get('label', field_name)
                
                logger.info(f"[AUDIT] Processing {field_name} (type: {field_type})")
                
                # Process the field based on type and collect change info
                change_info = process_field_change(
                    db, field_name, field_label, field_type, field_meta,
                    old_value, new_value
                )
                
                if change_info:
                    changes.append(change_info)
        
        # If we have changes, create audit log entry
        if changes:
            logger.info(f"[AUDIT] Creating audit log with {len(changes)} field changes")
            
            if len(changes) == 1:
                # Single field change - use legacy format for compatibility
                change = changes[0]
                audit_entry = AuditLog(
                    res_model=model_name,
                    res_id=record.id,
                    field_name=change['field_name'],
                    field_label=change['field_label'],
                    old_value=change['old_value'],
                    new_value=change['new_value'],
                    changes_json=None,
                    user_id=user_id,
                    changed_at=datetime.utcnow(),
                    change_type='write'
                )
                logger.info(f"[AUDIT] Created single field audit log entry for {change['field_name']}")
            else:
                # Multiple fields changed - use grouped format
                changes_data = json.dumps(changes, ensure_ascii=False)
                
                audit_entry = AuditLog(
                    res_model=model_name,
                    res_id=record.id,
                    field_name=None,
                    field_label=None,
                    old_value=None,
                    new_value=None,
                    changes_json=changes_data,
                    user_id=user_id,
                    changed_at=datetime.utcnow(),
                    change_type='write'
                )
                logger.info(f"[AUDIT] Created grouped audit log entry with {len(changes)} changes")
            
            db.add(audit_entry)
        
    except Exception as e:
        logger.error(f"Failed to track field changes: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")


def process_field_change(
    db: Session,
    field_name: str,
    field_label: str,
    field_type: str,
    field_meta: Dict,
    old_value: Any,
    new_value: Any
) -> Dict[str, Any] | None:
    """
    Process a single field change and return change info dict.
    Returns None if there's no actual change.
    """
    logger.info(f"[AUDIT]   Old value type: {type(old_value).__name__}, value: {old_value}")
    logger.info(f"[AUDIT]   New value type: {type(new_value).__name__}, value: {new_value}")
    
    # For Many2one fields, normalize values for comparison
    if field_type == "many2one":
        # Normalize old value to ID for comparison
        old_id = None
        if old_value is not None:
            if isinstance(old_value, int):
                old_id = old_value
            elif hasattr(old_value, 'id'):
                old_id = old_value.id
            elif isinstance(old_value, dict) and 'id' in old_value:
                old_id = old_value['id']
        
        # Normalize new value to ID for comparison
        new_id = None
        if new_value is not None:
            if isinstance(new_value, int):
                new_id = new_value
            elif hasattr(new_value, 'id'):
                new_id = new_value.id
            elif isinstance(new_value, dict) and 'id' in new_value:
                new_id = new_value['id']
        
        # Skip if IDs are the same (no actual change)
        if old_id == new_id:
            return None
        
        # For display, format the old value (object) and fetch new value display name
        old_value_display = format_value_for_audit(old_value, field_type, field_meta)
        
        # For new value, we need to fetch the display name from the database
        if new_id is not None:
            try:
                # Get the related model class
                comodel_name = field_meta.get('relation')
                if comodel_name:
                    from backend.core.registry import registry
                    related_model = registry.get_model(comodel_name)
                    if related_model:
                        related_record = db.query(related_model).filter(
                            related_model.id == new_id
                        ).first()
                        if related_record:
                            new_value_display = format_value_for_audit(
                                related_record, field_type, field_meta
                            )
                        else:
                            new_value_display = str(new_id)
                    else:
                        new_value_display = str(new_id)
                else:
                    new_value_display = str(new_id)
            except Exception as e:
                logger.warning(f"Failed to fetch display name for {field_name}: {e}")
                new_value_display = str(new_id)
        else:
            new_value_display = ""
        
        # Return change info
        return {
            'field_name': field_name,
            'field_label': field_label,
            'field_type': field_type,
            'old_value': old_value_display,
            'new_value': new_value_display
        }
    
    # For Many2many fields, normalize values for comparison
    elif field_type == "many2many":
        logger.info(f"[AUDIT] Many2many field detected: {field_name}")
        
        # Normalize old value to set of IDs
        old_ids = set()
        old_records = []
        if old_value is not None:
            logger.info(f"[AUDIT]   Old value is not None, type: {type(old_value)}")
            if isinstance(old_value, (list, tuple)):
                logger.info(f"[AUDIT]   Old value is list/tuple with {len(old_value)} items")
                for item in old_value:
                    if isinstance(item, int):
                        old_ids.add(item)
                    elif hasattr(item, 'id'):
                        old_ids.add(item.id)
                        old_records.append(item)
                    elif isinstance(item, dict) and 'id' in item:
                        old_ids.add(item['id'])
            elif hasattr(old_value, '__iter__'):
                logger.info(f"[AUDIT]   Old value is iterable")
                # Handle recordset-like objects
                for item in old_value:
                    if hasattr(item, 'id'):
                        old_ids.add(item.id)
                        old_records.append(item)
        
        logger.info(f"[AUDIT]   Old IDs: {old_ids}, Old records count: {len(old_records)}")
        
        # Normalize new value to set of IDs
        new_ids = set()
        new_records = []
        if new_value is not None:
            logger.info(f"[AUDIT]   New value is not None, type: {type(new_value)}")
            if isinstance(new_value, (list, tuple)):
                logger.info(f"[AUDIT]   New value is list/tuple with {len(new_value)} items")
                for item in new_value:
                    if isinstance(item, int):
                        new_ids.add(item)
                    elif isinstance(item, dict) and 'id' in item:
                        new_ids.add(item['id'])
                    elif hasattr(item, 'id'):
                        new_ids.add(item.id)
                        new_records.append(item)
            elif hasattr(new_value, '__iter__'):
                logger.info(f"[AUDIT]   New value is iterable")
                # Handle recordset-like objects
                for item in new_value:
                    if hasattr(item, 'id'):
                        new_ids.add(item.id)
                        new_records.append(item)
        
        logger.info(f"[AUDIT]   New IDs: {new_ids}, New records count: {len(new_records)}")
        
        # Skip if ID sets are the same (no actual change)
        if old_ids == new_ids:
            logger.info(f"[AUDIT]   Skipping {field_name} - IDs are the same")
            return None
        
        logger.info(f"[AUDIT]   IDs changed! Creating audit log for {field_name}")
        
        # Calculate what was added and removed
        added_ids = new_ids - old_ids
        removed_ids = old_ids - new_ids
        
        logger.info(f"[AUDIT]   Added IDs: {added_ids}")
        logger.info(f"[AUDIT]   Removed IDs: {removed_ids}")
        
        # Build display strings showing only changes
        changes = []
        
        # Get comodel for fetching records
        comodel_name = field_meta.get('relation')
        related_model = None
        if comodel_name:
            try:
                from backend.core.registry import registry
                related_model = registry.get_model(comodel_name)
            except Exception as e:
                logger.warning(f"Failed to get related model {comodel_name}: {e}")
        
        # Format removed items
        if removed_ids:
            removed_names = []
            # Try to get names from old_records first
            old_records_dict = {r.id: r for r in old_records if hasattr(r, 'id')}
            for rid in removed_ids:
                if rid in old_records_dict:
                    rec = old_records_dict[rid]
                    if hasattr(rec, 'display_name'):
                        removed_names.append(rec.display_name)
                    elif hasattr(rec, 'name'):
                        removed_names.append(rec.name)
                    else:
                        removed_names.append(f"ID {rid}")
                else:
                    # Try to fetch from database
                    if related_model:
                        try:
                            rec = db.query(related_model).filter(related_model.id == rid).first()
                            if rec:
                                if hasattr(rec, 'display_name'):
                                    removed_names.append(rec.display_name)
                                elif hasattr(rec, 'name'):
                                    removed_names.append(rec.name)
                                else:
                                    removed_names.append(f"ID {rid}")
                            else:
                                removed_names.append(f"ID {rid}")
                        except:
                            removed_names.append(f"ID {rid}")
                    else:
                        removed_names.append(f"ID {rid}")
            
            if removed_names:
                changes.append(f"Removed: {', '.join(removed_names)}")
        
        # Format added items
        if added_ids:
            added_names = []
            # Try to get names from new_records first
            new_records_dict = {r.id: r for r in new_records if hasattr(r, 'id')}
            for aid in added_ids:
                if aid in new_records_dict:
                    rec = new_records_dict[aid]
                    if hasattr(rec, 'display_name'):
                        added_names.append(rec.display_name)
                    elif hasattr(rec, 'name'):
                        added_names.append(rec.name)
                    else:
                        added_names.append(f"ID {aid}")
                else:
                    # Try to fetch from database
                    if related_model:
                        try:
                            rec = db.query(related_model).filter(related_model.id == aid).first()
                            if rec:
                                if hasattr(rec, 'display_name'):
                                    added_names.append(rec.display_name)
                                elif hasattr(rec, 'name'):
                                    added_names.append(rec.name)
                                else:
                                    added_names.append(f"ID {aid}")
                            else:
                                added_names.append(f"ID {aid}")
                        except:
                            added_names.append(f"ID {aid}")
                    else:
                        added_names.append(f"ID {aid}")
            
            if added_names:
                changes.append(f"Added: {', '.join(added_names)}")
        
        # Create display strings
        if removed_ids and not added_ids:
            # Only removals
            old_value_display = ""
            new_value_display = changes[0] if changes else "Updated"
        elif added_ids and not removed_ids:
            # Only additions
            old_value_display = ""
            new_value_display = changes[0] if changes else "Updated"
        else:
            # Both additions and removals - use newline to separate
            old_value_display = ""
            new_value_display = "\n".join(changes) if changes else "Updated"
        
        logger.info(f"[AUDIT]   Formatted old value: {old_value_display}")
        logger.info(f"[AUDIT]   Formatted new value: {new_value_display}")
        
        # Return change info
        return {
            'field_name': field_name,
            'field_label': field_label,
            'field_type': field_type,
            'old_value': old_value_display,
            'new_value': new_value_display
        }
    
    # For datetime/date fields, normalize format for comparison
    elif field_type in ("datetime", "date"):
        # Normalize old value
        old_normalized = None
        if old_value is not None:
            if isinstance(old_value, (datetime, date)):
                old_normalized = old_value
            elif isinstance(old_value, str):
                try:
                    # Parse ISO format or other common formats
                    old_value_clean = old_value.replace('Z', '+00:00').replace('T', ' ')
                    if field_type == "datetime":
                        old_normalized = datetime.fromisoformat(old_value_clean)
                    else:
                        old_normalized = datetime.fromisoformat(old_value_clean.split()[0]).date()
                except:
                    pass
        
        # Normalize new value
        new_normalized = None
        if new_value is not None:
            if isinstance(new_value, (datetime, date)):
                new_normalized = new_value
            elif isinstance(new_value, str):
                try:
                    new_value_clean = new_value.replace('Z', '+00:00').replace('T', ' ')
                    if field_type == "datetime":
                        new_normalized = datetime.fromisoformat(new_value_clean)
                    else:
                        new_normalized = datetime.fromisoformat(new_value_clean.split()[0]).date()
                except:
                    pass
        
        # Compare normalized values
        if old_normalized == new_normalized:
            return None
        
        # Format for display
        old_value_display = format_value_for_audit(old_normalized or old_value, field_type, field_meta)
        new_value_display = format_value_for_audit(new_normalized or new_value, field_type, field_meta)
        
        return {
            'field_name': field_name,
            'field_label': field_label,
            'field_type': field_type,
            'old_value': old_value_display,
            'new_value': new_value_display
        }
    
    else:
        # For other field types, format and return
        old_value_display = format_value_for_audit(old_value, field_type, field_meta)
        new_value_display = format_value_for_audit(new_value, field_type, field_meta)
        
        # Skip if values are the same
        if old_value_display == new_value_display:
            return None
        
        return {
            'field_name': field_name,
            'field_label': field_label,
            'field_type': field_type,
            'old_value': old_value_display,
            'new_value': new_value_display
        }
