"""
Metaclass for automatic field processing in models.
This processes Znova-style field definitions and generates SQLAlchemy columns and UI metadata.
"""

from sqlalchemy.ext.declarative import DeclarativeMeta
from .fields import BaseField


class ModelMeta(DeclarativeMeta):
    """
    Metaclass that processes field definitions and automatically generates
    SQLAlchemy columns and UI metadata.
    """
    
    def __new__(mcs, name, bases, namespace, **kwargs):
        # Extract field definitions
        field_definitions = {}
        columns_to_add = {}
        relationships_to_add = {}
        ui_metadata = {}
        
        # Get the model's tablename for Many2many relation_table generation
        model_tablename = namespace.get('__tablename__')
        
        # Find all field definitions in the class
        for attr_name, attr_value in list(namespace.items()):
            if isinstance(attr_value, BaseField):
                field_definitions[attr_name] = attr_value
                
                # Generate SQLAlchemy column
                column = attr_value.get_column(attr_name)
                if column is not None:
                    columns_to_add[attr_name] = column
                
                # Generate SQLAlchemy relationship
                relationship_def = attr_value.get_relationship(attr_name, model_class_name=name, model_tablename=model_tablename)
                if relationship_def is not None:
                    # Handle tuple format (rel_name, relationship_obj)
                    if isinstance(relationship_def, tuple) and len(relationship_def) == 2:
                        rel_name, rel_obj = relationship_def
                        relationships_to_add[rel_name] = rel_obj
                    else:
                        relationships_to_add[attr_name] = relationship_def
                
                # Generate UI metadata - pass model_tablename for Many2many fields
                if hasattr(attr_value, 'field_type') and attr_value.field_type == 'many2many':
                    ui_metadata[attr_name] = attr_value.get_ui_metadata(attr_name, model_tablename)
                else:
                    ui_metadata[attr_name] = attr_value.get_ui_metadata(attr_name)
                
                # Remove the field definition from namespace
                del namespace[attr_name]
        
        # Add generated columns and relationships to namespace
        namespace.update(columns_to_add)
        namespace.update(relationships_to_add)
        
        # Merge with existing _ui_metadata if present
        existing_metadata = namespace.get('_ui_metadata', {})
        existing_metadata.update(ui_metadata)
        namespace['_ui_metadata'] = existing_metadata
        
        # Store field definitions for reference
        namespace['_field_definitions'] = field_definitions
        
        # Build many2one relationship map: {field_name -> relationship_attr_name}
        # e.g. {'team_a_id': 'team_a', 'session_id': 'session'}
        m2o_rel_map = {}
        for attr_name, attr_value in field_definitions.items():
            if hasattr(attr_value, 'field_type') and attr_value.field_type == 'many2one':
                if attr_name.endswith('_id'):
                    rel_name = attr_name[:-3]
                else:
                    rel_name = f"{attr_name}_rel"
                m2o_rel_map[attr_name] = rel_name
        namespace['_m2o_rel_map'] = m2o_rel_map
        
        return super().__new__(mcs, name, bases, namespace, **kwargs)