from sqlalchemy import Column, Integer, DateTime, Text, and_, or_, not_
from datetime import datetime, date
from sqlalchemy.sql import func
from sqlalchemy.orm import Session, object_session
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from typing import List
from .database import Base, db_session
from .registry import registry
from .exceptions import UserError, ValidationError
from .domain_engine import domain_engine, ValidationResult
import logging
import base64
import re

logger = logging.getLogger(__name__)


class Environment:
    """
    Simulates Znova's self.env.
    Provides access to models and the database session.
    """
    def __init__(self, db: Session, user_id=None):
        self.db = db
        self.user_id = user_id
        self._user = None
        self.context = {}

    @property
    def user(self):
        if self._user is None and self.user_id:
            try:
                self._user = self['user'].browse(self.user_id)
            except Exception:
                # Fallback or silent fail if model not loaded yet
                return None
        return self._user

    def __getitem__(self, model_name):
        model_cls = registry.get_model(model_name)
        if not model_cls:
            raise KeyError(f"Model {model_name} not found in registry")
        return Recordset(model_cls, self)

    def with_context(self, **kwargs):
        new_env = Environment(self.db, user_id=self.user_id)
        new_env.context = {**self.context, **kwargs}
        return new_env


class Recordset:
    """
    Simulates Znova's recordset.
    Wraps a model and a list of records.
    """
    def __init__(self, model_cls, env, records=None):
        self._model = model_cls
        self.env = env
        self._records = records or []
        self._ids = [r.id for r in self._records] if records else []

    def __len__(self):
        return len(self._records)

    def __iter__(self):
        for record in self._records:
            yield Recordset(self._model, self.env, [record])

    def __getitem__(self, index):
        if isinstance(index, slice):
            return Recordset(self._model, self.env, self._records[index])
        return Recordset(self._model, self.env, [self._records[index]])

    def __getattr__(self, name):
        if len(self) == 1:
            return getattr(self._records[0], name)
        elif len(self) == 0:
            return None
        raise AttributeError(f"Multiple records in recordset, use ensure_one() or iterate.")

    def ensure_one(self):
        if len(self) != 1:
            raise UserError(f"Expected singleton recordset, got {len(self)} records.")
        return self

    def exists(self):
        return Recordset(self._model, self.env, [r for r in self._records if r in self.env.db])

    def ids(self):
        return self._ids

    def search(self, domain=None, limit=None, order=None):
        query = self.env.db.query(self._model)
        
        if domain:
            query = self._model.apply_domain_to_query(query, domain, env=self.env)
        
        if order:
            # Support SQL-style order strings like "priority asc, next_call desc".
            for o in order.split(','):
                o = o.strip()
                if not o:
                    continue

                parts = o.split()
                field_name = parts[0]
                direction = parts[1].lower() if len(parts) > 1 else "asc"
                column = getattr(self._model, field_name)

                if direction == "desc":
                    query = query.order_by(column.desc())
                else:
                    query = query.order_by(column.asc())
                    
        if limit:
            query = query.limit(limit)
            
        return Recordset(self._model, self.env, query.all())

    def browse(self, ids):
        if isinstance(ids, int):
            ids = [ids]
        records = self.env.db.query(self._model).filter(self._model.id.in_(ids)).all()
        return Recordset(self._model, self.env, records)

    def write(self, vals):
        for record in self._records:
            record.write(self.env.db, vals, user_id=self.env.user_id)
        return True

    def create(self, vals):
        record = self._model.create(self.env.db, vals)
        return Recordset(self._model, self.env, [record])

    def unlink(self):
        for record in self._records:
            self.env.db.delete(record)
        self.env.db.commit()
        return True

    def filtered(self, func):
        return Recordset(self._model, self.env, [r for r in self._records if func(r)])

    def mapped(self, path):
        if not self._records: return []
        res = []
        for r in self._records:
            val = r
            for part in path.split('.'):
                val = getattr(val, part)
            res.append(val)
        return res

    def sorted(self, key=None, reverse=False):
        return Recordset(self._model, self.env, sorted(self._records, key=key, reverse=reverse))


class BaseModel(Base):
    __abstract__ = True
    
    # Many2one relationship map: {field_name -> relationship_attr_name}
    # Populated by ModelMeta for ZnovaModel subclasses
    _m2o_rel_map = {}
    
    @classmethod
    def apply_domain_to_query(cls, query, domain, env=None):
        """
        Applies an Odoo-style domain (Polish notation) to a SQLAlchemy query.
        """
        if not domain:
            return query
            
        def resolve_value(val):
            if isinstance(val, str) and val.startswith('user.') and env and env.user:
                parts = val.split('.')
                resolved = env.user
                for part in parts[1:]:
                    if resolved is not None and hasattr(resolved, part):
                        resolved = getattr(resolved, part)
                    else:
                        resolved = None
                        break
                return resolved if resolved is not None else val
            return val

        def condition_to_filter(item):
            if not (isinstance(item, (list, tuple)) and len(item) == 3):
                return None
            field, op, value = item
            
            # Resolve user context in value
            value = resolve_value(value)

            if '.' in field:
                parts = field.split('.')
                if len(parts) == 2:
                    m2o_field, related_field_name = parts
                    m2o_rel_name = cls._m2o_rel_map.get(m2o_field)
                    if m2o_rel_name and hasattr(cls, m2o_rel_name):
                        rel_attr = getattr(cls, m2o_rel_name)
                        related_model = rel_attr.property.mapper.class_
                        if hasattr(related_model, related_field_name):
                            target_attr = getattr(related_model, related_field_name)

                            if op == '=':
                                return rel_attr.has(target_attr == value)
                            if op == '!=':
                                return ~rel_attr.has(target_attr == value)
                            if op == 'in':
                                return rel_attr.has(target_attr.in_(value))
                            if op == 'not in':
                                return ~rel_attr.has(target_attr.in_(value))
                            if op == 'like':
                                return rel_attr.has(target_attr.like(f"%{value}%"))
                            if op == 'ilike':
                                return rel_attr.has(target_attr.ilike(f"%{value}%"))
                            if op == '>':
                                return rel_attr.has(target_attr > value)
                            if op == '<':
                                return rel_attr.has(target_attr < value)
                            if op == '>=':
                                return rel_attr.has(target_attr >= value)
                            if op == '<=':
                                return rel_attr.has(target_attr <= value)
                return None
            
            if not hasattr(cls, field):
                return None
            attr = getattr(cls, field)
            
            # Detect if this is a relationship attribute (Many2many or One2many)
            from sqlalchemy.orm import RelationshipProperty
            is_rel = hasattr(attr, "property") and isinstance(attr.property, RelationshipProperty)
            
            if is_rel:
                # Basic relationship filtering support
                related_model = attr.property.mapper.class_
                
                # Normalize values: if it's a list/tuple of dicts with 'id', extract IDs
                # If it's a single dict with 'id', extract ID
                def normalize_id(v):
                    if isinstance(v, dict) and 'id' in v:
                        return v['id']
                    return v

                if isinstance(value, (list, tuple)):
                    val_to_use = [normalize_id(v) for v in value]
                else:
                    val_to_use = normalize_id(value)

                if op == 'in':
                    if not isinstance(val_to_use, (list, tuple)): val_to_use = [val_to_use]
                    # Filter out None values to avoid SQL errors
                    val_to_use = [v for v in val_to_use if v is not None]
                    if not val_to_use: return None
                    return attr.any(related_model.id.in_(val_to_use))
                elif op == 'not in':
                    if not isinstance(val_to_use, (list, tuple)): val_to_use = [val_to_use]
                    val_to_use = [v for v in val_to_use if v is not None]
                    if not val_to_use: return None
                    return ~attr.any(related_model.id.in_(val_to_use))
                elif op == '=':
                    if val_to_use is None or val_to_use is False:
                        return ~attr.any()
                    return attr.any(related_model.id == val_to_use)
                elif op == '!=':
                    if val_to_use is None or val_to_use is False:
                        return attr.any()
                    return ~attr.any(related_model.id == val_to_use)
                return None

            # Standard column handling
            # Handle "is None" / "is False" checks
            if (value is None or value is False) and op == "=":
                return attr.is_(None)
            elif (value is None or value is False) and op == "!=":
                return attr.isnot(None)
            elif op == '=': return attr == value
            elif op == '!=': return attr != value
            elif op == 'in': return attr.in_(value)
            elif op == 'not in': return ~attr.in_(value)
            elif op == 'like': return attr.like(f"%{value}%")
            elif op == 'ilike': return attr.ilike(f"%{value}%")
            elif op == '>': return attr > value
            elif op == '<': return attr < value
            elif op == '>=': return attr >= value
            elif op == '<=': return attr <= value
            return None

        def parse(tokens):
            if not tokens: return None
            token = tokens.pop(0)
            if token == '&':
                return and_(parse(tokens), parse(tokens))
            elif token == '|':
                return or_(parse(tokens), parse(tokens))
            elif token == '!':
                return not_(parse(tokens))
            else:
                return condition_to_filter(token)

        tokens = list(domain)
        filters = []
        while tokens:
            f = parse(tokens)
            if f is not None:
                filters.append(f)
        
        if filters:
            query = query.filter(and_(*filters))
        return query
    
    def __getattribute__(self, name):
        """
        Odoo-like many2one access: self.team_a_id returns the related record
        (relationship object) instead of the raw FK integer.
        To get the raw integer: self._raw_id('team_a_id')
        """
        # Fast path: skip for private/dunder attrs and known internals
        if name.startswith('_') or name in ('metadata', 'registry', 'id', 'env'):
            return super().__getattribute__(name)
        
        try:
            m2o_map = super().__getattribute__('_m2o_rel_map')
        except AttributeError:
            return super().__getattribute__(name)
        
        if name in m2o_map:
            rel_attr = m2o_map[name]
            try:
                return super().__getattribute__(rel_attr)
            except AttributeError:
                pass
        
        return super().__getattribute__(name)
    
    def _raw_id(self, field_name: str):
        """Get the raw FK integer value for a many2one field."""
        return super().__getattribute__(field_name)
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Metadata for UI rendering
    _ui_metadata = {}
    
    # View definitions (Znova-style structure)
    _ui_views = {
        "form": {
            "groups": [], # list of {title, fields[]}
            "tabs": []    # list of {title, fields[]}
        },
        "list": {
            "fields": []  # ordered list of fields
        }
    }

    @classmethod
    def get_env(cls, db: Session = None):
        db = db or db_session
        return Environment(db)

    @property
    def env(self):
        if hasattr(self, '_custom_env') and self._custom_env:
            return self._custom_env
        session = object_session(self) or db_session
        return Environment(session)

    @classmethod
    def search(cls, domain=None, limit=None, order=None, db: Session = None, user_id=None):
        """Standard Znova search method that returns a Recordset"""
        db = db or db_session
        return Environment(db, user_id=user_id)[cls._model_name_].search(domain=domain, limit=limit, order=order)

    @classmethod
    def browse(cls, ids, db: Session = None, user_id=None):
        """Standard Znova browse method that returns a Recordset"""
        db = db or db_session
        return Environment(db, user_id=user_id)[cls._model_name_].browse(ids)

    # ---------------------------------------------------------
    # Znova-style Shims for single records
    # ---------------------------------------------------------
    def ensure_one(self):
        return self

    def exists(self):
        ins = inspect(self)
        return not ins.deleted and not ins.detached

    def filtered(self, func):
        return Recordset(type(self), self.env, [self] if func(self) else [])

    def mapped(self, path):
        val = self
        for part in path.split('.'):
            val = getattr(val, part)
        return [val]

    def sorted(self, key=None, reverse=False):
        return Recordset(type(self), self.env, [self])

    @classmethod
    def default_get(cls, fields_list: list) -> dict:
        """
        Standard Znova default_get. Returns a dictionary of defaults.
        """
        defaults = {}
        # Get field definitions from metaclass
        field_defs = getattr(cls, '_field_definitions', {})
        
        for field_name in fields_list:
            field_def = field_defs.get(field_name)
            if not field_def:
                continue
            
            # Skip attachment fields - they don't have defaults
            if field_def.field_type in ("attachment", "attachments"):
                continue
                
            if field_def.default is not None:
                if callable(field_def.default):
                    # We pass the class to callable if it expects it?
                    # Odoo normally doesn't pass anything or passes self if it's a method
                    # But since this is a class level default, no instance exists.
                    defaults[field_name] = field_def.default()
                else:
                    defaults[field_name] = field_def.default
            
        return defaults

    @classmethod
    def _parse_values(cls, vals: dict):
        """
        Parses raw values (str, etc) into Python types based on metadata.
        Filters out read-only properties and relational fields (one2many, many2many).
        """
        parsed = vals.copy()
        meta = cls._ui_metadata
        valid_data = {}
        
        for key, value in parsed.items():
            # Filter read-only properties
            prop = getattr(cls, key, None)
            if isinstance(prop, property) and prop.fset is None:
                continue
            
            field_meta = meta.get(key, {})
            field_type = field_meta.get("type")
            
            # Skip relational fields (one2many, many2many) - these are handled separately
            if field_type in ("one2many", "many2many"):
                continue
            
            # Skip if not a column or recognized field (simple check)
            # Actually, we should probably allow properties that have setters, 
            # allowing the model to handle them in __init__ if custom logic exists.
            # For now, we trust provided keys unless they are read-only properties.

            if value is None or value == "":
                valid_data[key] = None
                continue
            
            try:
                if field_type == "many2one" and isinstance(value, dict):
                    valid_data[key] = value.get("id")
                elif field_type == "date" and isinstance(value, str):
                    valid_data[key] = date.fromisoformat(value.split('T')[0])
                elif field_type == "datetime" and isinstance(value, str):
                    val = value.replace('Z', '+00:00')
                    valid_data[key] = datetime.fromisoformat(val)
                elif field_type == "image" and isinstance(value, str):
                    # Validate and store Base64 image data
                    valid_data[key] = cls._validate_image_data(value, field_meta)
                else:
                    valid_data[key] = value
            except (ValueError, TypeError) as e:
                # Fallback
                valid_data[key] = value
        
        return valid_data

    @classmethod
    def _validate_record_deletion(cls, db: Session, record):
        """
        Validate if a record can be safely deleted.
        Check for required relationships and other constraints.
        
        Args:
            db: Database session
            record: The record to be deleted
            
        Raises:
            UserError: If the record cannot be deleted due to constraints
        """
        record_class = type(record)
        
        # Check if this record is referenced by other records with required relationships
        # This is a basic implementation - can be extended based on specific business rules
        
        # For now, we'll allow deletion but clean up relationships
        # In the future, you can add specific validation rules here
        # For example:
        # if hasattr(record, 'status') and record.status == 'in_progress':
        #     raise UserError("Cannot delete records that are in progress")
        
        pass

    @classmethod
    def _cleanup_many2many_relationships(cls, db: Session, record):
        """
        Clean up Many2many relationships for a record before deletion.
        
        Args:
            db: Database session
            record: The record that will be deleted
        """
        from sqlalchemy import text
        
        # Get the record's model class
        record_class = type(record)
        
        # Find all Many2many fields in the record's metadata
        for field_name, field_meta in record_class._ui_metadata.items():
            if field_meta.get("type") == "many2many":
                relation_table = field_meta.get("relation_table")
                if relation_table:
                    # Get column names
                    col1 = field_meta.get("column1") or f"{record_class.__tablename__}_id"
                    
                    # Delete all relationships for this record
                    delete_sql = text(f"""
                        DELETE FROM {relation_table}
                        WHERE {col1} = :record_id
                    """)
                    db.execute(delete_sql, {'record_id': record.id})

    @classmethod
    def _process_relational_fields(cls, db: Session, record, relational_data: dict, is_create: bool = False):
        """
        Process one2many and many2many field operations.
        
        Args:
            db: Database session
            record: The parent record
            relational_data: Dictionary of relational field operations
            is_create: Whether this is a create operation (vs update)
        """
        from .registry import registry
        
        for field_name, operations in relational_data.items():
            field_meta = cls._ui_metadata.get(field_name, {})
            field_type = field_meta.get("type")
            
            if field_type == "one2many":
                # Handle one2many operations
                relation_model_name = field_meta.get("relation")
                inverse_field = field_meta.get("inverse_name")
                
                if not relation_model_name or not inverse_field:
                    logger.warning(f"One2many field {field_name} missing relation or inverse_name metadata")
                    continue
                
                relation_model = registry.get_model(relation_model_name)
                if not relation_model:
                    logger.warning(f"Related model {relation_model_name} not found in registry")
                    continue
                
                # Process create operations
                if isinstance(operations, dict) and 'create' in operations:
                    for create_vals in operations['create']:
                        # Set the inverse field to link to parent
                        create_vals[inverse_field] = record.id
                        relation_model.create(db, create_vals)
                
                # Process update operations
                if isinstance(operations, dict) and 'update' in operations:
                    for update_vals in operations['update']:
                        if 'id' in update_vals:
                            related_id = update_vals.pop('id')
                            related_record = db.query(relation_model).filter(relation_model.id == related_id).first()
                            if related_record:
                                related_record.write(db, update_vals)
                
                # Process delete operations
                if isinstance(operations, dict) and 'delete' in operations:
                    delete_ids = operations['delete']
                    if delete_ids:
                        # Validate deletion - check for required relationships
                        for record_id in delete_ids:
                            record_to_delete = db.query(relation_model).filter(relation_model.id == record_id).first()
                            if record_to_delete:
                                cls._validate_record_deletion(db, record_to_delete)
                        
                        # Before deleting records, clean up their Many2many relationships
                        for record_id in delete_ids:
                            record_to_delete = db.query(relation_model).filter(relation_model.id == record_id).first()
                            if record_to_delete:
                                # Clean up Many2many relationships for this record
                                cls._cleanup_many2many_relationships(db, record_to_delete)
                        
                        # Now delete the records
                        db.query(relation_model).filter(relation_model.id.in_(delete_ids)).delete(synchronize_session=False)
            
            elif field_type == "many2many":
                # Handle many2many operations
                relation_model_name = field_meta.get("relation")
                relation_table = field_meta.get("relation_table")
                
                if not relation_model_name or not relation_table:
                    logger.warning(f"Many2many field {field_name} missing relation or relation_table metadata")
                    continue
                
                relation_model = registry.get_model(relation_model_name)
                if not relation_model:
                    logger.warning(f"Related model {relation_model_name} not found in registry")
                    continue
                
                col1 = field_meta.get("column1") or f"{cls.__tablename__}_id"
                col2 = field_meta.get("column2") or f"{relation_model.__tablename__}_id"
                
                logger.info(f"DEBUG M2M: field={field_name} table={relation_table} col1={col1} col2={col2}")
                
                from sqlalchemy import text
                
                # Handle list assignment (replace all)
                if isinstance(operations, list):
                    # Normalize IDs
                    def get_id(v):
                        if isinstance(v, dict): return v.get('id')
                        return v
                    target_ids = [get_id(v) for v in operations if get_id(v) is not None]
                    
                    try:
                        # Clear existing relations
                        db.execute(
                            text(f"DELETE FROM {relation_table} WHERE {col1} = :sid"),
                            {"sid": record.id}
                        )
                        # Insert new ones
                        for tid in target_ids:
                            db.execute(
                                text(f"INSERT INTO {relation_table} ({col1}, {col2}) VALUES (:sid, :tid)"),
                                {"sid": record.id, "tid": tid}
                            )
                        logger.info(f"SUCCESSfully synchronized M2M {field_name} for {cls.__name__}:{record.id}")
                    except Exception as e:
                        logger.error(f"Error synchronizing Many2many {field_name}: {e}")
                
                # Process add operations
                elif isinstance(operations, dict) and 'add' in operations:
                    add_ids = operations['add']
                    for tid in add_ids:
                        try:
                            # Check if exists first to avoid duplicates
                            check_sql = text(f"SELECT 1 FROM {relation_table} WHERE {col1} = :sid AND {col2} = :tid")
                            exists = db.execute(check_sql, {"sid": record.id, "tid": tid}).fetchone()
                            if not exists:
                                db.execute(
                                    text(f"INSERT INTO {relation_table} ({col1}, {col2}) VALUES (:sid, :tid)"),
                                    {"sid": record.id, "tid": tid}
                                )
                        except Exception as e:
                            logger.error(f"Error adding M2M {field_name}: {e}")
                
                # Process remove operations
                if isinstance(operations, dict) and 'remove' in operations:
                    remove_ids = operations['remove']
                    if remove_ids:
                        try:
                            # Delete from junction table
                            db.execute(
                                text(f"DELETE FROM {relation_table} WHERE {col1} = :sid AND {col2} IN :tids"),
                                {"sid": record.id, "tids": tuple(remove_ids)}
                            )
                        except Exception as e:
                            logger.error(f"Error removing M2M {field_name}: {e}")
            
            elif field_type in ("attachment", "attachments"):
                # Handle attachment fields - create/update ir.attachment records
                if operations is None:
                    continue
                
                logger.info(f"Processing {field_type} field '{field_name}' with operations: {operations}")
                    
                # Get the ir.attachment model
                attachment_model = registry.get_model("ir.attachment")
                if not attachment_model:
                    logger.warning("ir.attachment model not found in registry")
                    continue
                
                # Get current attachments for this field
                current_attachments = db.query(attachment_model).filter(
                    attachment_model.res_model == cls._model_name_,
                    attachment_model.res_id == record.id,
                    attachment_model.res_field == field_name
                ).all()
                current_attachment_ids = {att.id for att in current_attachments}
                
                logger.info(f"Current attachments for {field_name}: {current_attachment_ids}")
                
                # For single attachment field, operations is a single attachment ID or dict
                # For multiple attachments field, operations is a list
                if field_type == "attachment":
                    # Single attachment - operations is either None, int, or dict
                    attachments_to_process = [operations] if operations else []
                else:
                    # Multiple attachments - operations is a list
                    attachments_to_process = operations if isinstance(operations, list) else []
                
                logger.info(f"Attachments to process for {field_name}: {attachments_to_process}")
                
                # Track which attachment IDs should remain
                keep_attachment_ids = set()
                
                for attachment_data in attachments_to_process:
                    if isinstance(attachment_data, dict):
                        # Check if this is an update (has 'id') or create (no 'id')
                        if 'id' in attachment_data:
                            # Update existing attachment
                            att_id = attachment_data.pop('id')
                            existing_attachment = db.query(attachment_model).filter(attachment_model.id == att_id).first()
                            if existing_attachment:
                                logger.info(f"Updating existing attachment ID: {att_id}")
                                existing_attachment.write(db, attachment_data)
                                keep_attachment_ids.add(att_id)
                        else:
                            # Create new attachment
                            attachment_data.update({
                                'res_model': cls._model_name_,
                                'res_id': record.id,
                                'res_field': field_name
                            })
                            logger.info(f"Creating new attachment with data: {attachment_data}")
                            created_attachment = attachment_model.create(db, attachment_data)
                            logger.info(f"Created attachment ID: {created_attachment.id}")
                            keep_attachment_ids.add(created_attachment.id)
                    elif isinstance(attachment_data, int):
                        # Existing attachment ID - just keep it
                        logger.info(f"Keeping existing attachment ID: {attachment_data}")
                        keep_attachment_ids.add(attachment_data)
                        
                        # Make sure it's linked to this record (in case it was uploaded but not yet linked)
                        existing_attachment = db.query(attachment_model).filter(attachment_model.id == attachment_data).first()
                        if existing_attachment and (existing_attachment.res_id != record.id or existing_attachment.res_model != cls._model_name_):
                            logger.info(f"Linking attachment {attachment_data} to {cls._model_name_}:{record.id}")
                            existing_attachment.write(db, {
                                'res_model': cls._model_name_,
                                'res_id': record.id,
                                'res_field': field_name
                            })
                
                # Delete attachments that were removed
                attachments_to_delete = current_attachment_ids - keep_attachment_ids
                if attachments_to_delete:
                    logger.info(f"Deleting removed attachments: {attachments_to_delete}")
                    db.query(attachment_model).filter(attachment_model.id.in_(attachments_to_delete)).delete(synchronize_session=False)

    @classmethod
    def _get_image_field_defaults(cls):
        """
        Get default configuration values for image fields.
        
        Returns:
            dict: Default image field configuration
        """
        return {
            "max_size": 5242880,  # 5MB in bytes
            "allowed_formats": ["jpeg", "jpg", "png", "gif", "webp"],
            "display_width": 120,
            "display_height": 120,
            "required": False
        }

    @classmethod
    def _validate_image_field_config(cls, field_name: str, field_meta: dict):
        """
        Validates image field configuration and applies defaults.
        
        Args:
            field_name: Name of the image field
            field_meta: Field metadata to validate
            
        Returns:
            dict: Validated and normalized field metadata
            
        Raises:
            ValidationError: If configuration is invalid
        """
        if field_meta.get("type") != "image":
            return field_meta
            
        # Start with defaults
        defaults = cls._get_image_field_defaults()
        validated_config = defaults.copy()
        
        # Override with provided values
        for key, value in field_meta.items():
            if key in defaults:
                validated_config[key] = value
            else:
                # Keep non-image-specific metadata (label, invisible, etc.)
                validated_config[key] = value
        
        # Validate configuration values
        max_size = validated_config.get("max_size")
        if not isinstance(max_size, int) or max_size <= 0:
            raise ValidationError(f"Image field '{field_name}': max_size must be a positive integer")
        if max_size > 50 * 1024 * 1024:  # 50MB limit
            raise ValidationError(f"Image field '{field_name}': max_size cannot exceed 50MB (52428800 bytes)")
            
        allowed_formats = validated_config.get("allowed_formats")
        if not isinstance(allowed_formats, list) or not allowed_formats:
            raise ValidationError(f"Image field '{field_name}': allowed_formats must be a non-empty list")
        
        valid_formats = {"jpeg", "jpg", "png", "gif", "webp", "bmp", "tiff"}
        for fmt in allowed_formats:
            if not isinstance(fmt, str) or fmt.lower() not in valid_formats:
                raise ValidationError(f"Image field '{field_name}': unsupported format '{fmt}'. Valid formats: {', '.join(valid_formats)}")
        
        # Normalize formats to lowercase
        validated_config["allowed_formats"] = [fmt.lower() for fmt in allowed_formats]
        
        display_width = validated_config.get("display_width")
        if not isinstance(display_width, int) or display_width <= 0:
            raise ValidationError(f"Image field '{field_name}': display_width must be a positive integer")
        if display_width > 1000:
            raise ValidationError(f"Image field '{field_name}': display_width cannot exceed 1000 pixels")
            
        display_height = validated_config.get("display_height")
        if not isinstance(display_height, int) or display_height <= 0:
            raise ValidationError(f"Image field '{field_name}': display_height must be a positive integer")
        if display_height > 1000:
            raise ValidationError(f"Image field '{field_name}': display_height cannot exceed 1000 pixels")
        
        return validated_config

    @classmethod
    def _validate_image_data(cls, image_data: str, field_meta: dict):
        """
        Validates Base64 image data according to field metadata constraints.
        
        Args:
            image_data: Base64 encoded image string (with or without data URL prefix)
            field_meta: Field metadata containing validation rules
            
        Returns:
            str: Validated Base64 image data with data URL prefix
            
        Raises:
            ValidationError: If image data is invalid
        """
        if not image_data:
            return None
            
        # Ensure field metadata has proper defaults
        validated_meta = cls._validate_image_field_config("temp_field", field_meta)
            
        # Extract Base64 data from data URL if present
        if image_data.startswith('data:'):
            # Format: data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD...
            try:
                header, b64_data = image_data.split(',', 1)
                mime_type = header.split(';')[0].split(':')[1]
            except (ValueError, IndexError):
                raise ValidationError("Invalid image data format")
        else:
            # Assume raw Base64 data, try to detect format
            b64_data = image_data
            mime_type = None
            
        # Validate Base64 format
        try:
            decoded_data = base64.b64decode(b64_data, validate=True)
        except Exception:
            raise ValidationError("Invalid Base64 image data")
            
        # Check file size limits
        max_size = validated_meta.get("max_size", 5242880)  # Default 5MB
        if len(decoded_data) > max_size:
            raise ValidationError(f"Image size ({len(decoded_data)} bytes) exceeds maximum allowed size ({max_size} bytes)")
            
        # Detect image format from binary data if not provided
        if not mime_type:
            if decoded_data.startswith(b'\xff\xd8\xff'):
                mime_type = 'image/jpeg'
            elif decoded_data.startswith(b'\x89PNG\r\n\x1a\n'):
                mime_type = 'image/png'
            elif decoded_data.startswith(b'GIF87a') or decoded_data.startswith(b'GIF89a'):
                mime_type = 'image/gif'
            elif decoded_data.startswith(b'RIFF') and b'WEBP' in decoded_data[:12]:
                mime_type = 'image/webp'
            else:
                raise ValidationError("Unsupported image format")
                
        # Validate allowed formats
        allowed_formats = validated_meta.get("allowed_formats", ["jpeg", "jpg", "png", "gif", "webp"])
        format_name = mime_type.split('/')[-1]
        if format_name not in allowed_formats and not (format_name == 'jpeg' and 'jpg' in allowed_formats):
            raise ValidationError(f"Image format '{format_name}' not allowed. Supported formats: {', '.join(allowed_formats)}")
            
        # Return properly formatted data URL
        return f"data:{mime_type};base64,{b64_data}"

    @classmethod
    def trigger_onchange(cls, vals: dict, field_name: str, db: Session = None):
        """
        API helper to simulate onchanges on a dummy record.
        """
        # Create a temporary record
        record = cls()
        record._onchange_raw_values = {}
        if db:
            # Use _custom_env because env is a read-only property
            record._custom_env = Environment(db)
        
        # Set values - handle many2one relationships
        field_defs = getattr(cls, '_field_definitions', {})
        for k, v in vals.items():
            if hasattr(record, k):
                try:
                    # Handle dictionary values for Many2one fields (extract ID)
                    field_def = field_defs.get(k)
                    if field_def and field_def.field_type in ('one2many', 'many2many') and isinstance(v, list):
                        record._onchange_raw_values[k] = v
                        continue
                    if field_def and field_def.field_type == 'many2one' and isinstance(v, dict):
                        v = v.get('id')

                    setattr(record, k, v)
                    
                    # If it's a many2one, try to load the relationship object for code that uses it
                    if db and field_def and field_def.field_type == 'many2one' and v:
                        rel_attr = field_def.get_ui_metadata(k).get('relation_attr')
                        if rel_attr and hasattr(record, rel_attr):
                            from .registry import registry
                            rel_model = registry.get_model(field_def.comodel_name)
                            if rel_model:
                                # Use db.get() if available (SQLAlchemy 1.4+), otherwise query.get()
                                try:
                                    rel_obj = db.get(rel_model, v)
                                except AttributeError:
                                    rel_obj = db.query(rel_model).get(v)
                                if rel_obj:
                                    setattr(record, rel_attr, rel_obj)
                except Exception as e:
                    logger.debug(f"Error setting {k}={v} in onchange: {e}")
        
        # Apply onchanges for the specific field
        record._apply_onchanges(field_name)
        
        # Apply computes for non-stored fields so UI gets updated values
        record._recompute_all(stored_only=False)
        
        # Return the resulting dict with domain states
        result = record.to_dict(include_domain_states=True)
        
        # Filter out attachment fields - they should not be changed by onchange
        # and returning them causes the frontend to overwrite with empty values
        filtered_result = {}
        for key, value in result.items():
            field_meta = cls._ui_metadata.get(key, {})
            field_type = field_meta.get("type")
            if field_type not in ("attachment", "attachments"):
                filtered_result[key] = value
        
        return filtered_result

    def _recompute_all(self, stored_only=False):
        """
        Recompute all computed fields.
        if stored_only=True, only recomputes fields with store=True.
        """
        field_defs = getattr(self, '_field_definitions', {})
        for field_name, field_def in field_defs.items():
            if field_def.compute:
                if stored_only and not field_def.store:
                    continue
                
                method = getattr(self, field_def.compute, None)
                if method:
                    try:
                        method()
                    except Exception as e:
                        logger.error(f"Error computing field {field_name} in {type(self).__name__}: {e}")

    def _apply_onchanges(self, field_name: str = None):
        """
        Triggers onchange methods.
        """
        # Find all methods with _onchange attribute
        for attr_name in dir(self):
            if attr_name.startswith('__'):
                continue
            attr = getattr(self, attr_name, None)
            if attr and hasattr(attr, '_onchange'):
                if not field_name or field_name in attr._onchange:
                    try:
                        attr()
                    except Exception as e:
                        logger.error(f"Error in onchange {attr_name} in {type(self).__name__}: {e}")

    @classmethod
    def create(cls, *args, **kwargs):
        """
        Creates a new record.
        Flexible signature: create(db, vals) or create(vals)
        """
        if len(args) == 2 and isinstance(args[0], Session):
            db, vals = args
        elif len(args) == 1 and isinstance(args[0], dict):
            db = db_session
            vals = args[0]
        elif 'vals' in kwargs:
            vals = kwargs['vals']
            db = kwargs.get('db') or db_session
        else:
            raise TypeError("create() takes 1 or 2 arguments (vals: dict, db: Session = None)")

        # Get user_id for audit tracking
        user_id = kwargs.get('user_id')

        relational_data = {}
        regular_vals = {}
        
        for key, value in vals.items():
            field_meta = cls._ui_metadata.get(key, {})
            field_type = field_meta.get("type")
            
            # Separate relational and virtual fields from regular database columns
            if field_type in ("one2many", "many2many", "attachment", "attachments"):
                relational_data[key] = value
            else:
                regular_vals[key] = value
        
        # Parse regular values
        data = cls._parse_values(regular_vals)

        # Merge defaults
        defaults = cls.default_get(cls._field_definitions.keys())
        for k, v in defaults.items():
            if k not in data:
                data[k] = v
        
        # Pre-check for unique constraints (Optimistic check)
        # We check all columns that have unique=True and are present in data
        for col in cls.__table__.columns:
            if col.unique and col.name in data and data[col.name] is not None:
                existing = db.query(cls).filter(getattr(cls, col.name) == data[col.name]).first()
                if existing:
                    raise UserError(f"The {cls._ui_metadata.get(col.name, {}).get('label', col.name)} '{data[col.name]}' already exists.")

        try:
            # Create the main record first. Ignore virtual/unknown keys that are not table columns.
            column_names = {col.name for col in cls.__table__.columns}
            record = cls(**{k: v for k, v in data.items() if k in column_names})
            
            db.add(record)
            db.flush()  # Flush to get the ID and load relationships
            
            # Now recompute stored fields — relationships are resolvable after flush
            db.refresh(record)
            record._recompute_all(stored_only=True)
            db.flush()  # Flush computed values
            
            # Process relational fields
            cls._process_relational_fields(db, record, relational_data, is_create=True)
            
            # Track record creation in audit log
            if user_id:
                from .audit_tracker import track_record_creation
                track_record_creation(db, cls, record, user_id)
            
            db.commit()
            db.refresh(record)
            return record
        except IntegrityError as e:
            db.rollback()
            # If our pre-check failed (race condition), catch it here
            msg = str(e.orig) if hasattr(e, 'orig') else str(e)
            
            # Handle foreign key constraint violations with user-friendly messages
            if "foreign key constraint" in msg.lower():
                if "violates foreign key constraint" in msg and "is still referenced" in msg:
                    raise UserError("Cannot delete this record because it has related data that depends on it. Please remove the related data first or contact your administrator.")
                else:
                    raise UserError(f"Cannot complete this operation due to data relationships. Details: {msg}")
            elif "unique constraint" in msg.lower():
                raise UserError(f"A record with same key values already exists. Details: {msg}")
            else:
                raise ValidationError(f"Database error: {msg}")
        except Exception as e:
            db.rollback()
            raise e

    def write(self, *args, **kwargs):
        """
        Updates the record.
        Flexible signature: write(db, vals) or write(vals)
        Optional kwargs: user_id for audit tracking
        """
        if len(args) == 2 and isinstance(args[0], Session):
            db, vals = args
        elif len(args) == 1 and isinstance(args[0], dict):
            db = object_session(self) or db_session
            vals = args[0]
        elif 'vals' in kwargs:
            vals = kwargs.pop('vals')  # Remove vals from kwargs
            db = kwargs.pop('db', None) or object_session(self) or db_session
        else:
            raise TypeError("write() takes 1 or 2 arguments (vals: dict, db: Session = None)")

        # Get user_id for audit tracking (from kwargs)
        user_id = kwargs.get('user_id') or getattr(self, '_audit_user_id', None)
        
        # Capture old values for audit tracking
        old_values = {}
        if user_id:
            from .audit_tracker import get_tracked_fields
            tracked_fields = get_tracked_fields(type(self))
            for field_name in tracked_fields.keys():
                if hasattr(self, field_name):
                    old_values[field_name] = getattr(self, field_name)

        # Separate relational fields from regular fields
        relational_data = {}
        regular_vals = {}
        
        for key, value in vals.items():
            field_meta = self._ui_metadata.get(key, {})
            field_type = field_meta.get("type")
            
            # Separate relational and virtual fields from regular database columns
            if field_type in ("one2many", "many2many", "attachment", "attachments"):
                relational_data[key] = value
            else:
                regular_vals[key] = value
        
        data = self._parse_values(regular_vals)
        
        # Pre-check unique on update
        for col in self.__table__.columns:
            if col.unique and col.name in data and data[col.name] is not None:
                # Check if changed
                if getattr(self, col.name) != data[col.name]:
                     # Check if other record has this value
                     existing = db.query(type(self)).filter(
                         getattr(type(self), col.name) == data[col.name],
                         getattr(type(self), "id") != self.id
                     ).first()
                     if existing:
                         raise UserError(f"The {self._ui_metadata.get(col.name, {}).get('label', col.name)} '{data[col.name]}' already exists.")

        try:
            # Update regular fields
            for key, value in data.items():
                if hasattr(self, key):
                     setattr(self, key, value)
            
            db.flush()  # Flush FK updates so relationships refresh
            
            # Refresh to load new relationship objects, then recompute
            db.refresh(self)
            self._recompute_all(stored_only=True)
            db.flush()  # Flush computed values
            
            # Process relational fields
            self._process_relational_fields(db, self, relational_data, is_create=False)
            
            # Track field changes in audit log
            if user_id and old_values:
                from .audit_tracker import track_field_changes
                logger.info(f"[AUDIT] About to track changes for record ID: {self.id}")
                # For many2many fields, we need to get the current values after processing
                # Merge regular vals with current many2many values from the record
                vals_with_current = vals.copy()
                for field_name in relational_data.keys():
                    if hasattr(self, field_name):
                        vals_with_current[field_name] = getattr(self, field_name)
                track_field_changes(db, type(self), self, old_values, vals_with_current, user_id)
            
            db.commit()
            db.refresh(self)
            return True
        except IntegrityError as e:
            db.rollback()
            msg = str(e.orig) if hasattr(e, 'orig') else str(e)
            
            # Handle foreign key constraint violations with user-friendly messages
            if "foreign key constraint" in msg.lower():
                if "violates foreign key constraint" in msg and "is still referenced" in msg:
                    raise UserError("Cannot delete this record because it has related data that depends on it. Please remove the related data first or contact your administrator.")
                else:
                    raise UserError(f"Cannot complete this operation due to data relationships. Details: {msg}")
            elif "unique constraint" in msg.lower():
                raise UserError(f"Duplicate value error. Details: {msg}")
            else:
                raise ValidationError(f"Database update error: {msg}")
        except Exception as e:
            db.rollback()
            raise e

    def unlink(self, db: Session = None):
        """Standard Znova unlink method for a single record"""
        db = db or object_session(self) or db_session
        try:
            db.delete(self)
            db.commit()
            return True
        except IntegrityError as e:
            db.rollback()
            msg = str(e.orig) if hasattr(e, 'orig') else str(e)
            if "foreign key constraint" in msg.lower():
                raise UserError("Cannot delete this record because it has related data that depends on it.")
            raise ValidationError(f"Database delete error: {msg}")
        except Exception as e:
            db.rollback()
            raise e

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        
        # Check if the class explicitly defines __abstract__ in its own __dict__
        # If not, it's inheriting from BaseModel and should not be considered abstract
        abstract_in_class = '__abstract__' in cls.__dict__ and cls.__dict__['__abstract__']
        tablename = getattr(cls, '__tablename__', None)
        
        # Skip registration for abstract models (only if explicitly set in the class itself)
        if abstract_in_class or tablename is None:
            return
            
        # Use explicit name if provided, else class name lowercase
        model_name = getattr(cls, "_model_name_", cls.__name__.lower())
        registry.register(model_name, cls)

    @classmethod
    def get_ui_metadata(cls, user_role=None):
        """
        Returns metadata and view definitions with domain expression validation.
        Also validates and normalizes image field configurations.
        """
        # Validate domain expressions in metadata
        validated_metadata = cls._validate_domain_expressions()
        
        # Validate and normalize image field configurations
        normalized_metadata = {}
        for field_name, field_meta in validated_metadata.items():
            if field_meta.get("type") == "image":
                try:
                    normalized_metadata[field_name] = cls._validate_image_field_config(field_name, field_meta)
                except ValidationError as e:
                    logger.warning(f"Image field configuration error for {cls.__name__}.{field_name}: {e}")
                    # Use defaults for invalid configuration
                    defaults = cls._get_image_field_defaults()
                    normalized_field = field_meta.copy()
                    # Replace invalid values with defaults
                    for key, default_value in defaults.items():
                        normalized_field[key] = default_value
                    # Keep non-image-specific metadata (label, invisible, etc.)
                    for key, value in field_meta.items():
                        if key not in defaults:
                            normalized_field[key] = value
                    normalized_metadata[field_name] = normalized_field
            else:
                normalized_metadata[field_name] = field_meta
            
            # Enrich relational fields with target model's rec_name
            if field_meta.get("type") in ("many2one", "one2many", "many2many"):
                relation_model_name = field_meta.get("relation")
                if relation_model_name:
                    from .registry import registry
                    rel_model = registry.get_model(relation_model_name)
                    if rel_model:
                        # Get target model's _name_field_ or use guessing logic
                        target_rec_name = getattr(rel_model, "_name_field_", None)
                        if not target_rec_name:
                            # Simple guess for the target model too
                            for cand in ["name", "full_name", "subject", "title"]:
                                if hasattr(rel_model, cand):
                                    target_rec_name = cand
                                    break
                        normalized_metadata[field_name]["rec_name"] = target_rec_name or "id"
        
        # Discover onchange-decorated methods and mark fields in metadata
        for attr_name in dir(cls):
            if attr_name.startswith('__'):
                continue
            attr = getattr(cls, attr_name, None)
            
            # Check @api.onchange
            if attr and hasattr(attr, '_onchange'):
                for field_name in attr._onchange:
                    if field_name in normalized_metadata:
                        normalized_metadata[field_name]['onchange'] = True
            
            # Check @api.depends and mark dependencies as onchange triggers
            if attr and hasattr(attr, '_depends'):
                for field_name in attr._depends:
                    # Dependencies might be dot-separated (e.g. 'partner_id.name'), 
                    # we only care about the root field on this model for onchange triggering
                    root_field = field_name.split('.')[0]
                    if root_field in normalized_metadata:
                        normalized_metadata[root_field]['onchange'] = True

        # Determine the display name field (rec_name)
        rec_name = getattr(cls, "_name_field_", None)
        if not rec_name:
            # Fallback guessing logic (on backend once, for all frontend)
            guess_candidates = ["name", "full_name", "subject", "title", "label"]
            for candidate in guess_candidates:
                if candidate in normalized_metadata:
                    rec_name = candidate
                    break
            if not rec_name:
                rec_name = "id"

        # Determine the status field
        status_field = getattr(cls, "_status_field_", None)
        if not status_field:
            if "status" in normalized_metadata:
                status_field = "status"
            elif "state" in normalized_metadata:
                status_field = "state"

        return {
            "description": getattr(cls, "_description_", cls.__name__),
            "fields": normalized_metadata,
            "views": cls._ui_views,
            "rec_name": rec_name,
            "status_field": status_field,
            "transient": getattr(cls, "_transient", False)
        }

    @classmethod
    def _validate_domain_expressions(cls):
        """
        Validate domain expressions in field metadata and return processed metadata.
        Supports both domain expressions and boolean values for invisible/readonly/required.
        """
        validated_metadata = {}
        available_fields = list(cls._ui_metadata.keys())
        
        # Add user context fields to available fields for validation
        user_context_fields = ['user']  # Just add 'user' as base field for dot notation
        available_fields.extend(user_context_fields)
        
        for field_name, field_meta in cls._ui_metadata.items():
            # Copy field metadata
            validated_field = field_meta.copy()
            
            # Validate invisible (supports both boolean and domain expression)
            if 'invisible' in field_meta:
                invisible_value = field_meta['invisible']
                if isinstance(invisible_value, bool):
                    # Boolean value - keep as is
                    validated_field['invisible'] = invisible_value
                elif isinstance(invisible_value, str) and invisible_value:
                    # Domain expression - validate
                    validation_result = domain_engine.validate_expression(
                        invisible_value, available_fields
                    )
                    if not validation_result.is_valid:
                        logger.warning(
                            f"Invalid invisible expression for {cls.__name__}.{field_name}: "
                            f"{', '.join(validation_result.errors)}"
                        )
                        # Remove invalid expression to prevent frontend errors
                        validated_field.pop('invisible', None)
                    elif validation_result.warnings:
                        for warning in validation_result.warnings:
                            logger.warning(
                                f"Warning in invisible expression for {cls.__name__}.{field_name}: {warning}"
                            )
            
            # Validate readonly (supports both boolean and domain expression)
            if 'readonly' in field_meta:
                readonly_value = field_meta['readonly']
                if isinstance(readonly_value, bool):
                    # Boolean value - keep as is
                    validated_field['readonly'] = readonly_value
                elif isinstance(readonly_value, str) and readonly_value:
                    # Domain expression - validate
                    validation_result = domain_engine.validate_expression(
                        readonly_value, available_fields
                    )
                    if not validation_result.is_valid:
                        logger.warning(
                            f"Invalid readonly expression for {cls.__name__}.{field_name}: "
                            f"{', '.join(validation_result.errors)}"
                        )
                        # Remove invalid expression to prevent frontend errors
                        validated_field.pop('readonly', None)
                    elif validation_result.warnings:
                        for warning in validation_result.warnings:
                            logger.warning(
                                f"Warning in readonly expression for {cls.__name__}.{field_name}: {warning}"
                            )
            
            # Validate required (supports both boolean and domain expression)
            if 'required' in field_meta:
                required_value = field_meta['required']
                if isinstance(required_value, bool):
                    # Boolean value - keep as is
                    validated_field['required'] = required_value
                elif isinstance(required_value, str) and required_value:
                    # Domain expression - validate
                    validation_result = domain_engine.validate_expression(
                        required_value, available_fields
                    )
                    if not validation_result.is_valid:
                        logger.warning(
                            f"Invalid required expression for {cls.__name__}.{field_name}: "
                            f"{', '.join(validation_result.errors)}"
                        )
                        # Remove invalid expression to prevent frontend errors
                        validated_field.pop('required', None)
                    elif validation_result.warnings:
                        for warning in validation_result.warnings:
                            logger.warning(
                                f"Warning in required expression for {cls.__name__}.{field_name}: {warning}"
                            )
            
            validated_metadata[field_name] = validated_field
        
        return validated_metadata

    @classmethod
    def get_field_metadata(cls, field_name: str, user_role=None):
        """
        Get metadata for a specific field with domain expression validation and image field normalization.
        
        Args:
            field_name: Name of the field
            user_role: User role for permission checking (future use)
            
        Returns:
            Dictionary containing field metadata
        """
        validated_metadata = cls._validate_domain_expressions()
        field_meta = validated_metadata.get(field_name, {})
        
        # Apply image field configuration validation and defaults
        try:
            return cls._validate_image_field_config(field_name, field_meta)
        except ValidationError as e:
            logger.warning(f"Image field configuration error for {cls.__name__}.{field_name}: {e}")
            # Return defaults for invalid image field configuration
            if field_meta.get("type") == "image":
                defaults = cls._get_image_field_defaults()
                normalized_field = field_meta.copy()
                # Replace invalid values with defaults
                for key, default_value in defaults.items():
                    normalized_field[key] = default_value
                # Keep non-image-specific metadata (label, invisible, etc.)
                for key, value in field_meta.items():
                    if key not in defaults:
                        normalized_field[key] = value
                return normalized_field
            return field_meta

    @classmethod
    def get_domain_fields(cls):
        """
        Get list of fields that have domain expressions (invisible, readonly, or required).
        
        Returns:
            Dictionary with 'invisible', 'readonly', and 'required' keys containing field lists
        """
        domain_fields = {
            'invisible': [],
            'readonly': [],
            'required': []
        }
        
        for field_name, field_meta in cls._ui_metadata.items():
            if field_meta.get('invisible') and isinstance(field_meta.get('invisible'), str):
                domain_fields['invisible'].append(field_name)
            if field_meta.get('readonly') and isinstance(field_meta.get('readonly'), str):
                domain_fields['readonly'].append(field_name)
            if field_meta.get('required') and isinstance(field_meta.get('required'), str):
                domain_fields['required'].append(field_name)
        
        return domain_fields

    @classmethod
    def evaluate_field_visibility(cls, field_name: str, context: dict, user_context: dict = None):
        """
        Evaluate field visibility based on domain expression or boolean value.
        
        Args:
            field_name: Name of the field
            context: Form data context for evaluation
            user_context: User information context
            
        Returns:
            Boolean indicating if field should be visible (True) or hidden (False)
        """
        field_meta = cls._ui_metadata.get(field_name, {})
        invisible_value = field_meta.get('invisible')
        
        if invisible_value is None:
            return True  # No value means always visible
        
        if isinstance(invisible_value, bool):
            return not invisible_value  # If invisible=True, field is hidden
        
        if isinstance(invisible_value, str):
            try:
                # If invisible expression evaluates to True, field should be hidden
                is_invisible = domain_engine.safe_evaluate(invisible_value, context, default=False, user_context=user_context)
                return not is_invisible
            except Exception as e:
                logger.warning(f"Error evaluating visibility for {cls.__name__}.{field_name}: {e}")
                return True  # Default to visible on error
        
        return True  # Default to visible

    @classmethod
    def evaluate_field_readonly(cls, field_name: str, context: dict, user_context: dict = None):
        """
        Evaluate field readonly state based on domain expression or boolean value.
        
        Args:
            field_name: Name of the field
            context: Form data context for evaluation
            user_context: User information context
            
        Returns:
            Boolean indicating if field should be readonly (True) or editable (False)
        """
        field_meta = cls._ui_metadata.get(field_name, {})
        readonly_value = field_meta.get('readonly')
        
        if readonly_value is None:
            return False  # No value means always editable
        
        if isinstance(readonly_value, bool):
            return readonly_value  # Direct boolean value
        
        if isinstance(readonly_value, str):
            try:
                return domain_engine.safe_evaluate(readonly_value, context, default=False, user_context=user_context)
            except Exception as e:
                logger.warning(f"Error evaluating readonly state for {cls.__name__}.{field_name}: {e}")
                return False  # Default to editable on error
        
        return False  # Default to editable

    @classmethod
    def evaluate_field_required(cls, field_name: str, context: dict, user_context: dict = None):
        """
        Evaluate field required state based on domain expression or boolean value.
        
        Args:
            field_name: Name of the field
            context: Form data context for evaluation
            user_context: User information context
            
        Returns:
            Boolean indicating if field is required (True) or optional (False)
        """
        field_meta = cls._ui_metadata.get(field_name, {})
        required_value = field_meta.get('required')
        
        if required_value is None:
            return False  # No value means optional
        
        if isinstance(required_value, bool):
            return required_value  # Direct boolean value
        
        if isinstance(required_value, str):
            try:
                return domain_engine.safe_evaluate(required_value, context, default=False, user_context=user_context)
            except Exception as e:
                logger.warning(f"Error evaluating required state for {cls.__name__}.{field_name}: {e}")
                return False  # Default to optional on error
        
        return False  # Default to optional

    @classmethod
    def get_metadata_with_context(cls, context: dict = None, user_role=None, user_context: dict = None):
        """
        Get metadata with evaluated domain expressions for given context and user.
        Also validates and normalizes image field configurations.
        
        Args:
            context: Form data context for domain evaluation
            user_role: User role for permission checking
            user_context: User information context (id, role, groups, etc.)
            
        Returns:
            Dictionary containing metadata with evaluated visibility, readonly, and required states
        """
        if context is None:
            context = {}
        
        validated_metadata = cls._validate_domain_expressions()
        
        # Apply image field configuration validation and defaults
        normalized_metadata = {}
        for field_name, field_meta in validated_metadata.items():
            if field_meta.get("type") == "image":
                try:
                    normalized_metadata[field_name] = cls._validate_image_field_config(field_name, field_meta)
                except ValidationError as e:
                    logger.warning(f"Image field configuration error for {cls.__name__}.{field_name}: {e}")
                    # Use defaults for invalid configuration
                    defaults = cls._get_image_field_defaults()
                    normalized_field = field_meta.copy()
                    # Replace invalid values with defaults
                    for key, default_value in defaults.items():
                        normalized_field[key] = default_value
                    # Keep non-image-specific metadata (label, invisible, etc.)
                    for key, value in field_meta.items():
                        if key not in defaults:
                            normalized_field[key] = value
                    normalized_metadata[field_name] = normalized_field
            else:
                normalized_metadata[field_name] = field_meta
        
        evaluated_metadata = {}
        for field_name, field_meta in normalized_metadata.items():
            evaluated_field = field_meta.copy()
            
            # Add evaluated states
            evaluated_field['is_visible'] = cls.evaluate_field_visibility(field_name, context, user_context)
            evaluated_field['is_readonly'] = cls.evaluate_field_readonly(field_name, context, user_context)
            evaluated_field['is_required'] = cls.evaluate_field_required(field_name, context, user_context)
            
            evaluated_metadata[field_name] = evaluated_field
        
        return {
            "fields": evaluated_metadata,
            "views": cls._ui_views,
            "domain_fields": cls.get_domain_fields()
        }

    @property
    def display_name(self):
        """Returns a string representation for UI display."""
        return (
            getattr(self, "name", None) or 
            getattr(self, "full_name", None) or 
            getattr(self, "subject", None) or 
            f"{type(self).__name__}({self.id})"
        )

    def to_dict(self, fields=None, user_role=None, include_domain_states=False, user_context=None, max_depth=1):
        """
        Convert ORM to dict, respecting field-level permissions and domain expressions.
        
        Args:
            fields: List of fields to include (None for all metadata fields)
            user_role: User role for permission checking
            include_domain_states: Whether to include visibility/readonly evaluation
            user_context: User information context for domain evaluation
            max_depth: Maximum recursion depth for related objects (O2M/M2M)
        """
        from backend.core.registry import registry
        
        out = {}
        target_fields = fields or self._ui_metadata.keys()
        
        # Get current record data as context for domain evaluation
        record_context = {}
        if include_domain_states:
            for field in self._ui_metadata.keys():
                if hasattr(self, field):
                    val = getattr(self, field)
                    # Convert to serializable format for domain evaluation
                    if isinstance(val, (datetime, date)):
                        record_context[field] = val.isoformat()
                    elif hasattr(val, 'id'):  # Many2one relationship
                        record_context[field] = {'id': val.id, 'display_name': str(val)}
                    else:
                        record_context[field] = val
        
        for field in target_fields:
            meta = self._ui_metadata.get(field, {})
            field_type = meta.get("type")
            
            # Recompute if needed (non-stored computed fields OR stored fields with empty depends)
            if meta.get('compute'):
                field_def = self._field_definitions.get(field)
                if field_def and field_def.compute:
                    method = getattr(self, field_def.compute, None)
                    
                    # Check if method has dependencies defined
                    # If depends is empty, always recompute on read (dynamic context-based fields)
                    depends = getattr(method, '_depends', ())
                    
                    if not meta.get('store') or not depends:
                        if method:
                            try:
                                method()
                            except Exception as e:
                                logger.error(f"Error computing field {field}: {e}")
            
            # Handle many2many fields - load from junction table
            if field_type == "many2many":
                relation_table = meta.get("relation_table")
                relation_model_name = meta.get("relation")
                raw_onchange_values = getattr(self, "_onchange_raw_values", {}) or {}

                if field in raw_onchange_values and isinstance(raw_onchange_values[field], list):
                    related_values = []
                    for related_record in raw_onchange_values[field]:
                        if isinstance(related_record, dict):
                            related_values.append(related_record)
                        elif hasattr(related_record, "to_dict"):
                            related_values.append(related_record.to_dict(
                                user_role=user_role,
                                include_domain_states=include_domain_states,
                                user_context=user_context,
                                max_depth=max_depth - 1
                            ))
                        else:
                            related_values.append(related_record)
                    out[field] = related_values
                    continue
                
                if relation_table and relation_model_name:
                    from sqlalchemy import text
                    relation_model = registry.get_model(relation_model_name)
                    if relation_model:
                        col1 = meta.get("column1") or f"{self.__tablename__}_id"
                        col2 = meta.get("column2") or f"{relation_model.__tablename__}_id"
                        
                        # Query junction table to get related IDs
                        query_sql = text(f"""
                            SELECT {col2} FROM {relation_table}
                            WHERE {col1} = :record_id
                        """)
                        
                        # Try to use the existing session first, fallback to new session
                        db = object_session(self)
                        if not db:
                            from backend.core.database import SessionLocal
                            db = SessionLocal()
                            should_close = True
                        else:
                            should_close = False
                            
                        try:
                            result = db.execute(query_sql, {'record_id': self.id})
                            related_ids = [row[0] for row in result]
                            out[field] = related_ids
                        except Exception as e:
                            logger.error(f"Error querying many2many field {field}: {e}")
                            out[field] = []
                        finally:
                            if should_close:
                                db.close()
                    else:
                        out[field] = []
                else:
                    out[field] = []
            
            # Handle one2many fields - load related records and convert to dict
            elif field_type == "one2many":
                relation_model_name = meta.get("relation")
                inverse_name = meta.get("inverse_name")
                raw_onchange_values = getattr(self, "_onchange_raw_values", {}) or {}

                if field in raw_onchange_values and isinstance(raw_onchange_values[field], list):
                    related_dicts = []
                    for related_record in raw_onchange_values[field]:
                        if isinstance(related_record, dict):
                            related_dicts.append(related_record)
                        elif hasattr(related_record, "to_dict"):
                            related_dicts.append(related_record.to_dict(
                                user_role=user_role,
                                include_domain_states=include_domain_states,
                                user_context=user_context,
                                max_depth=max_depth - 1
                            ))
                    out[field] = related_dicts
                    continue
                
                if relation_model_name and inverse_name and hasattr(self, field) and max_depth > 0:
                    related_records = getattr(self, field)
                    if related_records:
                        # Convert each related record to dict with decreased depth
                        related_dicts = []
                        for related_record in related_records:
                            related_dict = related_record.to_dict(
                                user_role=user_role, 
                                include_domain_states=include_domain_states, 
                                user_context=user_context,
                                max_depth=max_depth - 1
                            )
                            related_dicts.append(related_dict)
                        out[field] = related_dicts
                    else:
                        out[field] = []
                else:
                    out[field] = []
            
            # Handle attachment and attachments fields - load from ir.attachment
            elif field_type in ("attachment", "attachments"):
                attachment_model = registry.get_model("ir.attachment")
                
                if attachment_model:
                    db = object_session(self)
                    if not db:
                        from backend.core.database import SessionLocal
                        db = SessionLocal()
                        should_close = True
                    else:
                        should_close = False
                    
                    try:
                        # Query attachments for this record and field
                        attachments = db.query(attachment_model).filter(
                            attachment_model.res_model == self._model_name_,
                            attachment_model.res_id == self.id,
                            attachment_model.res_field == field
                        ).all()
                        
                        logger.info(f"Loading attachments for {self._model_name_}:{self.id} field '{field}': found {len(attachments)} attachments")
                        
                        if field_type == "attachment":
                            # Single attachment - return first one or None
                            if attachments:
                                attachment_dict = attachments[0].to_dict(max_depth=0)
                                out[field] = attachment_dict
                            else:
                                out[field] = None
                        else:
                            # Multiple attachments - return list
                            attachment_dicts = [att.to_dict(max_depth=0) for att in attachments]
                            logger.info(f"Returning {len(attachment_dicts)} attachments")
                            out[field] = attachment_dicts
                    except Exception as e:
                        logger.error(f"Error loading attachments for field {field}: {e}")
                        out[field] = [] if field_type == "attachments" else None
                    finally:
                        if should_close:
                            db.close()
                else:
                    logger.warning("ir.attachment model not found in registry")
                    out[field] = [] if field_type == "attachments" else None
            
            elif hasattr(self, field):
                val = getattr(self, field)
                
                # Check for many2one to provide a consistent {id, display_name} dict
                if meta.get("type") == "many2one" and val is not None:
                    # With __getattribute__ override, val is now the related record object
                    if hasattr(val, 'id'):
                        display_name = (
                            getattr(val, "name", None) or 
                            getattr(val, "full_name", None) or 
                            getattr(val, "subject", None) or 
                            str(val)
                        )
                        out[field] = {"id": val.id, "display_name": display_name}
                    else:
                        # Fallback: val is a raw integer (e.g., for non-ZnovaModel)
                        out[field] = val
                else:
                    # Handle data/datetime serialization
                    if isinstance(val, (datetime, date)):
                        out[field] = val.isoformat()
                    else:
                        out[field] = val
        
        if "id" not in out:
            out["id"] = self.id
        
        if "display_name" not in out:
            out["display_name"] = self.display_name
        
        # Add domain expression evaluation if requested
        if include_domain_states:
            domain_states = {}
            for field in target_fields:
                domain_states[field] = {
                    'is_visible': self.evaluate_field_visibility(field, record_context, user_context),
                    'is_readonly': self.evaluate_field_readonly(field, record_context, user_context),
                    'is_required': self.evaluate_field_required(field, record_context, user_context)
                }
            out['_domain_states'] = domain_states
            
        return out

    def notify_users(self, user_ids: List[int], title: str, message: str,
                    notification_type: str = "info", action: dict = None):
        """
        Send notification to users by user IDs from any model method.
        
        Args:
            user_ids: List of target user IDs
            title: Notification title
            message: Notification message content
            notification_type: Type of notification (info, success, warning, danger)
            action: Action configuration dict with type, target, and params
            
        Returns:
            List of created Notification instances
            
        Example:
            # From a Request model method
            equipment_handlers = db.query(User).filter(User.role.has(name="equipment_handler")).all()
            handler_ids = [user.id for user in equipment_handlers]
            
            request.notify_users(
                user_ids=handler_ids,
                title="New Equipment Request",
                message=f"New request: {request.subject}",
                notification_type="info",
                action={
                    "type": "navigate",
                    "target": f"/requests/{request.id}",
                    "params": {"highlight": True}
                }
            )
        """
        from backend.services.notification_service import get_notification_service
        from backend.core.websocket_manager import get_websocket_manager
        
        # Get the database session from the current object
        db = object_session(self)
        if not db:
            raise RuntimeError("No database session available for notification")
        
        # Get WebSocket manager for real-time notifications
        websocket_manager = get_websocket_manager()
        
        # Create notification service and send notifications
        # Note: created_by should be a user ID, not the current model's ID
        # We pass None here since we don't have a user context in model methods
        service = get_notification_service(db, websocket_manager)
        return service.notify_users(
            user_ids=user_ids,
            title=title,
            message=message,
            notification_type=notification_type,
            action=action,
            created_by=None  # System-generated notification, no specific creator
        )
    
    def notify_recordset(self, users, title: str, message: str,
                        notification_type: str = "info", action: dict = None):
        """
        Send notification to users from a recordset.
        
        Args:
            users: User recordset or list of User objects
            title: Notification title
            message: Notification message content
            notification_type: Type of notification (info, success, warning, danger)
            action: Action configuration dict with type, target, and params
            
        Returns:
            List of created Notification instances
            
        Example:
            # From a Request model method using recordset
            equipment_handlers = db.query(User).filter(User.role.has(name="equipment_handler")).all()
            
            request.notify_recordset(
                users=equipment_handlers,
                title="New Equipment Request",
                message=f"New request: {request.subject}",
                notification_type="info",
                action={
                    "type": "navigate", 
                    "target": f"/requests/{request.id}",
                    "params": {"highlight": True}
                }
            )
        """
        from backend.services.notification_service import get_notification_service
        from backend.core.websocket_manager import get_websocket_manager
        
        # Get the database session from the current object
        db = object_session(self)
        if not db:
            raise RuntimeError("No database session available for notification")
        
        # Get WebSocket manager for real-time notifications
        websocket_manager = get_websocket_manager()
        
        # Create notification service and send notifications
        # Note: created_by should be a user ID, not the current model's ID
        # We pass None here since we don't have a user context in model methods
        service = get_notification_service(db, websocket_manager)
        return service.notify_recordset(
            users=users,
            title=title,
            message=message,
            notification_type=notification_type,
            action=action,
            created_by=None  # System-generated notification, no specific creator
        )





# ==============================================================================
# ORM REFERENCE DOCUMENTATION
# ==============================================================================
"""
From an operational efficiency standpoint, these are the **high-frequency, business-critical ORM methods** that tend to sit at the core of day-to-day Znova development. Mastering these creates immediate leverage in delivery velocity and code quality.

---

## 🔹 Core Record Lifecycle Operations (High Utilization)

### **1. `create()`**
Strategic purpose: onboarding new business records into the system.
```python
record = self.env['res.partner'].create({
    'name': 'ABC Corp',
    'email': 'info@abc.com',
})
```
Used in: form submissions, wizards, automated workflows.

---

### **2. `write()`**
Strategic purpose: updating state while preserving data integrity.
```python
record.write({'active': False})
```
Used in: approvals, status transitions, bulk updates.

---

### **3. `unlink()`**
Strategic purpose: controlled data decommissioning.
```python
record.unlink()
```
Typically governed by access rules and business constraints.

---

## 🔹 Data Retrieval & Query Optimization

### **4. `search()`**
Strategic purpose: dataset discovery under defined business criteria.
```python
records = self.env['sale.order'].search([('state', '=', 'sale')])
```

---

### **5. `browse()`**
Strategic purpose: direct record hydration via known IDs.
```python
order = self.env['sale.order'].browse(15)
```
Zero database hit until field access — performance-friendly.

---

### **6. `search_read()`**
Strategic purpose: read-optimized fetch for UI/API layers.
```python
self.env['res.partner'].search_read(
    [('is_company', '=', True)],
    ['name', 'email']
)
```

---

### **7. `read()`**
Strategic purpose: structured data extraction from known records.
```python
record.read(['name', 'state'])
```

---

## 🔹 Business Logic & Validation Controls

### **8. `filtered()`**
Strategic purpose: in-memory dataset refinement.
```python
confirmed = orders.filtered(lambda o: o.state == 'sale')
```

---

### **9. `mapped()`**
Strategic purpose: mass field extraction or relational traversal.
```python
emails = partners.mapped('email')
```

---

### **10. `sorted()`**
Strategic purpose: business-rule-driven ordering.
```python
orders.sorted(key=lambda o: o.date_order, reverse=True)
```

---

## 🔹 Relational & Navigation Methods

### **11. `ensure_one()`**
Strategic purpose: enforcing single-record execution guarantees.
```python
self.ensure_one()
```

---

### **12. `exists()`**
Strategic purpose: defensive programming against stale references.
```python
record.exists()
```

---

### **13. `copy()`**
Strategic purpose: record duplication with controlled variance.
```python
new_order = order.copy({'name': 'SO-COPY'})
```

---

## 🔹 Context & Environment Management

### **14. `with_context()`**
Strategic purpose: contextualizing behavior without side effects.
```python
self.with_context(lang='fr_FR')
```

---

### **15. `sudo()`**
Strategic purpose: privilege escalation for system-level operations.
```python
self.sudo().write({'state': 'done'})
```

---

## 🔹 Developer Productivity Accelerators

### **16. `default_get()`**
Strategic purpose: centralized default value orchestration.

---

### **17. `name_get()` / `name_search()`**
Strategic purpose: UX consistency and search relevance.

---

## 🔹 Daily-Use Power Pattern (Executive Summary)

> **Search → Filter → Map → Write**
> This pipeline underpins ~80% of real-world Znova business flows.

---

### Strategic Recommendation
If your objective is to **differentiate as a high-impact Znova engineer**, internalize not just *what* these methods do, but *when* and *why* to deploy each for **performance, scalability, and governance**.
"""
