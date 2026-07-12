"""
Znova-style model base class with simplified field definitions.
"""

from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.sql import func
from .base_model import BaseModel
from .model_metaclass import ModelMeta
from . import fields as field_types


class ZnovaModel(BaseModel, metaclass=ModelMeta):
    """
    Base model class that supports Znova-style field definitions.
    
    Example usage:
    
    class Task(ZnovaModel):
        __tablename__ = "task"
        
        name = field_types.Char(label="Task Name", required=True, size=100)
        description = field_types.Text(label="Description")
        user_id = field_types.Many2one("user", label="Assigned User")
        status = field_types.Selection([
            ('todo', 'To Do'),
            ('done', 'Done')
        ], label="Status", default="todo")
        deadline = field_types.Date(label="Deadline")
    """
    __abstract__ = True
    
    # Ensure SQLAlchemy knows this is abstract
    __tablename__ = None