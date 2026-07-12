"""
Znova-style field definitions for simplified model creation.
This module provides field classes that automatically generate both SQLAlchemy columns
and UI metadata.
"""

from sqlalchemy import Column, String, Text as SQLText, Date as SQLDate, DateTime as SQLDateTime, Boolean as SQLBoolean, ForeignKey, JSON as SQLJSON, Table
from sqlalchemy import Integer as SQLInteger
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from backend.core.database import Base
from backend.core.registry import registry


CORE_TABLE_ALIASES = {
    "user": "users",
}


class BaseField:
    """Base class for all field types"""
    
    def __init__(self, label: str = None, required: Union[bool, str] = False, 
                 readonly: Union[bool, str] = False, invisible: Union[bool, str] = False, 
                 help: str = None, default: Any = None, domain: str = None, 
                 widget: str = None, compute: str = None, store: bool = None, 
                 onchange: str = None, tracking: bool = False, **kwargs):
        self.label = label
        self.required = required
        self.readonly = readonly
        self.invisible = invisible
        self.help = help
        self.default = default
        self.domain = domain
        self.widget = widget
        self.compute = compute
        # Default store to True if not provided, unless compute is set
        self.store = store if store is not None else (False if compute else True)
        self.onchange = onchange
        self.tracking = tracking  # Track field changes in audit log
        self.kwargs = kwargs
    
    def get_column(self, field_name: str) -> Column:
        """Generate SQLAlchemy column"""
        raise NotImplementedError

    @property
    def _is_always_required(self) -> bool:
        """Conditional required expressions are UI rules, not database NOT NULL."""
        return self.required is True
    
    def get_ui_metadata(self, field_name: str) -> Dict[str, Any]:
        """Generate UI metadata"""
        metadata = {
            "label": self.label or field_name.replace('_', ' ').title(),
            "type": self.field_type,
            "required": self.required,
        }
        
        if self.readonly is not False:
            metadata["readonly"] = self.readonly
        if self.invisible is not False:
            metadata["invisible"] = self.invisible
        if self.help:
            metadata["help"] = self.help
        if self.default is not None:
            metadata["default"] = self.default
        if self.domain:
            metadata["domain"] = self.domain
        if self.widget:
            metadata["widget"] = self.widget
        if self.compute:
            metadata["compute"] = self.compute
            metadata["store"] = self.store
        if self.onchange:
            metadata["onchange"] = self.onchange
        if self.tracking:
            metadata["tracking"] = self.tracking
            
        # Add any additional kwargs to metadata
        for key, value in self.kwargs.items():
            if key not in metadata:
                metadata[key] = value
            
        return metadata
    
    def get_relationship(self, field_name: str, model_class_name: str = None, model_tablename: str = None):
        """Generate SQLAlchemy relationship (to be overridden by relational fields)"""
        return None


class Char(BaseField):
    """Character field (string)"""
    field_type = "string"
    
    def __init__(self, size: int = 255, **kwargs):
        super().__init__(**kwargs)
        self.size = size
    
    def get_column(self, field_name: str) -> Column:
        if not self.store:
            return None
        return Column(String(self.size), nullable=not self._is_always_required, default=self.default)


class Text(BaseField):
    """Text field (multiline string)"""
    field_type = "text"
    
    def get_column(self, field_name: str) -> Column:
        if not self.store:
            return None
        return Column(SQLText, nullable=not self._is_always_required, default=self.default)


class Integer(BaseField):
    """Integer field"""
    field_type = "integer"
    
    def get_column(self, field_name: str) -> Column:
        if not self.store:
            return None
        return Column(SQLInteger, nullable=not self._is_always_required, default=self.default)


class Boolean(BaseField):
    """Boolean field"""
    field_type = "boolean"
    
    def get_column(self, field_name: str) -> Column:
        if not self.store:
            return None
        return Column(SQLBoolean, nullable=not self._is_always_required, default=self.default)


class Date(BaseField):
    """Date field"""
    field_type = "date"
    
    def get_column(self, field_name: str) -> Column:
        if not self.store:
            return None
        return Column(SQLDate, nullable=not self._is_always_required, default=self.default)


class DateTime(BaseField):
    """DateTime field"""
    field_type = "datetime"
    
    def get_column(self, field_name: str) -> Column:
        if not self.store:
            return None
        return Column(SQLDateTime, nullable=not self._is_always_required, default=self.default)


class JSON(BaseField):
    """JSON field"""
    field_type = "json"

    def get_column(self, field_name: str) -> Column:
        if not self.store:
            return None
        return Column(SQLJSON, nullable=not self._is_always_required, default=self.default)


class Selection(BaseField):
    """Selection field (dropdown)"""
    field_type = "selection"
    
    def __init__(self, selection: Union[List[tuple], Dict[str, Any]], **kwargs):
        # Extract options if provided separately
        self.options = kwargs.pop('options', None)
        super().__init__(**kwargs)
        self.selection = selection
    
    def get_column(self, field_name: str) -> Column:
        if not self.store:
            return None
        return Column(String(50), nullable=not self._is_always_required, default=self.default)
    
    def get_ui_metadata(self, field_name: str) -> Dict[str, Any]:
        metadata = super().get_ui_metadata(field_name)
        
        # Use explicitly provided options if available
        if self.options:
            metadata["options"] = self.options
        # Otherwise convert selection to options format
        elif isinstance(self.selection, list):
            # List of tuples: [('key', 'Label'), ...]
            metadata["options"] = {key: {"label": label} for key, label in self.selection}
        elif isinstance(self.selection, dict):
            # Already in options format
            metadata["options"] = self.selection
            
        return metadata


class Many2one(BaseField):
    """Many-to-one relationship field"""
    field_type = "many2one"
    
    def __init__(self, comodel_name: str, ondelete: str = "set null", use_alter: bool = False, class_name: str = None, **kwargs):
        super().__init__(**kwargs)
        self.comodel_name = comodel_name
        self.ondelete = ondelete
        self.use_alter = use_alter
        self.class_name = class_name
    
    def get_column(self, field_name: str) -> Column:
        if not self.store:
            return None
        # Generate foreign key column
        table_name = self._get_table_name(self.comodel_name)
        fk_name = f"fk_{field_name}_{table_name}" if self.use_alter else None
        return Column(
            SQLInteger,
            ForeignKey(f"{table_name}.id", ondelete=self.ondelete, use_alter=self.use_alter, name=fk_name),
            nullable=not self._is_always_required
        )
    
    def get_relationship(self, field_name: str, model_class_name: str = None, model_tablename: str = None):
        # Generate relationship using the field name without _id suffix as the relationship name
        # e.g., category_id -> category
        if field_name.endswith('_id'):
            rel_name = field_name[:-3]  # Remove '_id' suffix
        else:
            rel_name = f"{field_name}_rel"  # Add suffix if no _id
        
        class_name = self._get_class_name(self.comodel_name)
        # Use lazy='joined' for eager loading by default
        # Explicitly specify foreign_keys to avoid ambiguity when multiple relationships exist
        # Use string reference with class name to ensure correct resolution
        fk_ref = f"{model_class_name}.{field_name}" if model_class_name else field_name
        return (rel_name, relationship(class_name, lazy='joined', foreign_keys=fk_ref, overlaps="*"))
    
    def get_ui_metadata(self, field_name: str) -> Dict[str, Any]:
        metadata = super().get_ui_metadata(field_name)
        metadata["relation"] = self.comodel_name
        # Store the relationship attribute name for to_dict lookup
        if field_name.endswith('_id'):
            metadata["relation_attr"] = field_name[:-3]
        else:
            metadata["relation_attr"] = f"{field_name}_rel"
        return metadata
    
    def _get_table_name(self, comodel_name: str) -> str:
        """Convert model name to table name"""
        # First try to get the model from registry and use its table name
        model_cls = registry.get_model(comodel_name)
        if model_cls and hasattr(model_cls, '__tablename__'):
            return model_cls.__tablename__

        if comodel_name in CORE_TABLE_ALIASES:
            return CORE_TABLE_ALIASES[comodel_name]

        # Fallback to mapping for common models - CLEANED UP
        return comodel_name.replace(".", "_")
    
    def _get_class_name(self, comodel_name: str) -> str:
        """Convert model name to class name"""
        # First try to get the model from registry
        model_cls = registry.get_model(comodel_name)
        if model_cls:
            return model_cls.__name__
        
        if self.class_name:
            return self.class_name
        return _model_name_to_class_name(comodel_name)


class One2many(BaseField):
    """One-to-many relationship field with UI configuration"""
    field_type = "one2many"
    
    def __init__(self, comodel_name: str, inverse_name: str, 
                 columns: List[str] = None, editable: bool = True, 
                 create: bool = True, delete: bool = True, 
                 limit: int = None, show_label: bool = True, class_name: str = None, **kwargs):
        super().__init__(**kwargs)
        self.comodel_name = comodel_name
        self.inverse_name = inverse_name
        self.columns = columns or []
        self.editable = editable
        self.create = create
        self.delete = delete
        self.limit = limit
        self.show_label = show_label
        self.class_name = class_name
    
    def get_column(self, field_name: str) -> Column:
        # One2many doesn't create a column
        return None
    
    def get_relationship(self, field_name: str, model_class_name: str = None, model_tablename: str = None):
        """Generate SQLAlchemy relationship with explicit FK to avoid ambiguity."""
        class_name = self._get_class_name(self.comodel_name)
        return relationship(
            class_name,
            foreign_keys=f"[{class_name}.{self.inverse_name}]",
            lazy='select',
            viewonly=True,
            overlaps="*"
        )
    
    def get_ui_metadata(self, field_name: str) -> Dict[str, Any]:
        metadata = super().get_ui_metadata(field_name)
        metadata["relation"] = self.comodel_name
        metadata["inverse_name"] = self.inverse_name
        metadata["columns"] = self.columns
        metadata["editable"] = self.editable
        metadata["create"] = self.create
        metadata["delete"] = self.delete
        metadata["show_label"] = self.show_label
        if self.limit is not None:
            metadata["limit"] = self.limit
        return metadata
    
    def _get_class_name(self, comodel_name: str) -> str:
        """Convert model name to class name"""
        # First try to get the model from registry
        model_cls = registry.get_model(comodel_name)
        if model_cls:
            return model_cls.__name__
        
        if self.class_name:
            return self.class_name
        return _model_name_to_class_name(comodel_name)


class Many2many(BaseField):
    """Many-to-many relationship field with UI configuration"""
    field_type = "many2many"
    
    def __init__(self, comodel_name: str, relation_table: str = None, 
                 column1: str = None, column2: str = None, 
                 display_format: str = "pills", searchable: bool = True, 
                 create_inline: bool = True, relationship_kwargs: Dict[str, Any] = None,
                 class_name: str = None, **kwargs):
        super().__init__(**kwargs)
        self.comodel_name = comodel_name
        self.relation_table = relation_table  # Will be auto-generated if None
        self.column1 = column1  # Will be auto-generated if None
        self.column2 = column2  # Will be auto-generated if None
        self.display_format = display_format
        self.searchable = searchable
        self.create_inline = create_inline
        self.relationship_kwargs = relationship_kwargs or {}
        self.class_name = class_name
    
    def get_column(self, field_name: str) -> Column:
        # Many2many doesn't create a column
        return None
    
    def get_relationship(self, field_name: str, model_class_name: str = None, model_tablename: str = None):
        """Generate SQLAlchemy relationship with association table"""
        if not model_tablename or not model_class_name:
            return None
            
        comodel_table_name = self._get_table_name(self.comodel_name)
        
        # Calculate relation table name same way as UI metadata
        if self.relation_table:
            relation_table_name = self.relation_table
        else:
            tables = sorted([model_tablename, comodel_table_name])
            relation_table_name = f"{tables[0]}_{tables[1]}_rel"
            
        # Define association table if not exists
        if relation_table_name not in Base.metadata.tables:
            col1 = self.column1 or f"{model_tablename}_id"
            col2 = self.column2 or f"{comodel_table_name}_id"
            
            # Create association table dynamically
            association_table = Table(
                relation_table_name,
                Base.metadata,
                Column(col1, SQLInteger, ForeignKey(f"{model_tablename}.id"), primary_key=True),
                Column(col2, SQLInteger, ForeignKey(f"{comodel_table_name}.id"), primary_key=True),
                extend_existing=True
            )
        else:
            association_table = Base.metadata.tables[relation_table_name]
            
        comodel_class = self._get_class_name(self.comodel_name)
        
        # Use lazy='select' (default) instead of joined to avoid complex JOINs
        rel_kwargs = {'secondary': association_table, 'lazy': 'select'}
        if hasattr(self, 'relationship_kwargs'):
            rel_kwargs.update(self.relationship_kwargs)
            
        return relationship(comodel_class, **rel_kwargs)
    
    def get_ui_metadata(self, field_name: str, model_tablename: str = None) -> Dict[str, Any]:
        """
        Generate UI metadata with automatic relation_table name generation
        
        Args:
            field_name: Name of the field
            model_tablename: Table name of the model this field belongs to
        """
        metadata = super().get_ui_metadata(field_name)
        metadata["relation"] = self.comodel_name
        
        # Auto-generate relation_table if not provided
        if self.relation_table:
            relation_table = self.relation_table
        else:
            # Auto-generate: {model_table}_{comodel_table}_rel
            comodel_table = self._get_table_name(self.comodel_name)
            if model_tablename:
                # Sort alphabetically for consistency
                tables = sorted([model_tablename, comodel_table])
                relation_table = f"{tables[0]}_{tables[1]}_rel"
            else:
                # Fallback if model_tablename not provided
                relation_table = f"{field_name}_rel"
        
        metadata["relation_table"] = relation_table
        metadata["column1"] = self.column1 or f"{model_tablename}_id"
        metadata["column2"] = self.column2 or f"{comodel_table}_id"
        metadata["display_format"] = self.display_format
        metadata["searchable"] = self.searchable
        metadata["create_inline"] = self.create_inline
        
        return metadata
    
    def _get_table_name(self, comodel_name: str) -> str:
        """Convert model name to table name"""
        # First try to get the model from registry and use its table name
        model_cls = registry.get_model(comodel_name)
        if model_cls and hasattr(model_cls, '__tablename__'):
            return model_cls.__tablename__

        if comodel_name in CORE_TABLE_ALIASES:
            return CORE_TABLE_ALIASES[comodel_name]

        # Fallback to mapping for common models - CLEANED UP
        return comodel_name.replace(".", "_")
    
    def _get_class_name(self, comodel_name: str) -> str:
        """Convert model name to class name"""
        # First try to get the model from registry
        model_cls = registry.get_model(comodel_name)
        if model_cls:
            return model_cls.__name__
        
        if self.class_name:
            return self.class_name
        return _model_name_to_class_name(comodel_name)


class Image(BaseField):
    """Image field"""
    field_type = "image"
    
    def __init__(self, max_size: int = 5242880, allowed_formats: List[str] = None, 
                 display_width: int = 120, display_height: int = 120, **kwargs):
        super().__init__(**kwargs)
        self.max_size = max_size
        self.allowed_formats = allowed_formats or ["jpeg", "jpg", "png", "gif", "webp"]
        self.display_width = display_width
        self.display_height = display_height
    
    def get_column(self, field_name: str) -> Column:
        if not self.store:
            return None
        return Column(SQLText, nullable=not self._is_always_required)
    
    def get_ui_metadata(self, field_name: str) -> Dict[str, Any]:
        metadata = super().get_ui_metadata(field_name)
        metadata.update({
            "max_size": self.max_size,
            "allowed_formats": self.allowed_formats,
            "display_width": self.display_width,
            "display_height": self.display_height
        })
        return metadata


class Attachment(BaseField):
    """Single attachment field (One2many to ir.attachment with limit 1)"""
    field_type = "attachment"
    
    def __init__(self, max_size: int = 10485760, allowed_types: List[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.max_size = max_size  # 10MB default
        self.allowed_types = allowed_types  # e.g., ['pdf', 'doc', 'docx']
    
    def get_column(self, field_name: str) -> Column:
        # No column needed - uses ir.attachment relation
        return None
    
    def get_ui_metadata(self, field_name: str) -> Dict[str, Any]:
        metadata = super().get_ui_metadata(field_name)
        metadata.update({
            "relation": "ir.attachment",
            "max_size": self.max_size,
            "allowed_types": self.allowed_types,
            "multiple": False
        })
        return metadata


class Attachments(BaseField):
    """Multiple attachments field (One2many to ir.attachment)"""
    field_type = "attachments"
    
    def __init__(self, max_size: int = 10485760, allowed_types: List[str] = None, 
                 max_files: int = None, **kwargs):
        super().__init__(**kwargs)
        self.max_size = max_size  # 10MB per file default
        self.allowed_types = allowed_types
        self.max_files = max_files  # Optional limit on number of files
    
    def get_column(self, field_name: str) -> Column:
        # No column needed - uses ir.attachment relation
        return None
    
    def get_ui_metadata(self, field_name: str) -> Dict[str, Any]:
        metadata = super().get_ui_metadata(field_name)
        metadata.update({
            "relation": "ir.attachment",
            "max_size": self.max_size,
            "allowed_types": self.allowed_types,
            "max_files": self.max_files,
            "multiple": True
        })
        return metadata


def _model_name_to_class_name(model_name: str) -> str:
    """Convert dotted/snake model names to a conventional PascalCase class name."""
    parts = model_name.replace("_", ".").split(".")
    return "".join(part[:1].upper() + part[1:] for part in parts if part)


# Export field classes directly
__all__ = [
    'Char', 'Text', 'Integer', 'Boolean', 'Date', 'DateTime', 'JSON',
    'Selection', 'Many2one', 'One2many', 'Many2many', 'Image', 'Attachment', 'Attachments'
]
