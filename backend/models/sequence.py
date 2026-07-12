from sqlalchemy.orm import Session

from backend.core.base_model import Environment
from backend.core.znova_model import ZnovaModel
from backend.core import fields
from backend.core.exceptions import ValidationError, UserError
import re

class Sequence(ZnovaModel):
    __tablename__ = "sequences"
    _model_name_ = "sequence"
    _name_field_ = "name"
    
    name = fields.Char(label="Sequence Name", required=True, size=100, help="Human-readable name for this sequence")
    code = fields.Char(label="Sequence Code", required=True, size=100, help="Unique code to identify this sequence")
    prefix = fields.Char(label="Prefix", default="", size=20, help="Text to add before the number")
    suffix = fields.Char(label="Suffix", default="", size=20, help="Text to add after the number")
    padding = fields.Integer(label="Number Padding", default=5, help="Number of digits for the sequence number")
    number_next = fields.Integer(label="Next Number", default=1, help="Next number to be assigned")
    number_increment = fields.Integer(label="Increment", default=1, help="Step between sequence numbers")
    active = fields.Boolean(label="Active", default=True, help="Whether this sequence is active")
    implementation = fields.Selection([
        ("standard", "Standard"),
        ("no_gap", "No Gap")
    ], label="Implementation", default="standard", help="Standard allows gaps, No Gap ensures consecutive numbers")

    _role_permissions = {
        "admin": {
            "create": True,
            "read": True,
            "write": True,
            "delete": True,
            "domain": []
        },
        "user": {
            "create": False,
            "read": True,
            "write": False,
            "delete": False,
            "domain": []
        }
    }


    _ui_views = {
        "form": {
            "groups": [
                {
                    "title": "Sequence Information",
                    "fields": ["name", "code", "active"]
                },
                {
                    "title": "Format Configuration", 
                    "fields": ["prefix", "suffix", "padding"]
                },
                {
                    "title": "Number Configuration",
                    "fields": ["number_next", "number_increment", "implementation"]
                }
            ],
            "header_buttons": [
                {
                    "name": "preview_next",
                    "label": "Preview Next Number",
                    "type": "secondary",
                    "method": "action_preview_next"
                },
                {
                    "name": "reset_sequence",
                    "label": "Reset to 1",
                    "type": "warning",
                    "method": "action_reset_sequence"
                }
            ]
        },
        "list": {
            "fields": ["name", "code", "prefix", "number_next", "active"],
            "search_fields": ["name", "code"]
        }
    }

    @classmethod
    def create(cls, db: Session, vals: dict):
        """Override create to validate sequence configuration"""
        if 'code' in vals:
            code = vals['code']
            if not re.match(r'^[a-zA-Z0-9._-]+$', code):
                raise ValidationError("Sequence code can only contain letters, numbers, dots, underscores and hyphens")
        
        if 'padding' in vals and vals['padding'] < 1:
            raise ValidationError("Padding must be at least 1")
            
        if 'number_increment' in vals and vals['number_increment'] < 1:
            raise ValidationError("Number increment must be at least 1")
            
        return super().create(db, vals)

    def write(self, *args, **kwargs):
        """Override write to validate sequence configuration"""
        # Parse arguments (supporting both (db, vals) and (vals))
        db = None
        vals = {}
        
        if len(args) == 2:
            db, vals = args
        elif len(args) == 1:
            vals = args[0]
        else:
            vals = kwargs
            
        if 'code' in vals:
            code = vals['code']
            if not re.match(r'^[a-zA-Z0-9._-]+$', code):
                raise ValidationError("Sequence code can only contain letters, numbers, dots, underscores and hyphens")
        
        if 'padding' in vals and vals['padding'] < 1:
            raise ValidationError("Padding must be at least 1")
            
        if 'number_increment' in vals and vals['number_increment'] < 1:
            raise ValidationError("Number increment must be at least 1")
            
        return super().write(*args, **kwargs)

    def get_next_number(self):
        """Get the next number in the sequence and increment the counter."""
        self.ensure_one()
        if not self.active:
            raise UserError(f"Sequence '{self.code}' is not active")
            
        current_number = self.number_next
        padded_number = str(current_number).zfill(self.padding)
        sequence_value = f"{self.prefix or ''}{padded_number}{self.suffix or ''}"
        
        self.write({'number_next': self.number_next + self.number_increment})
        
        return sequence_value

    def preview_format(self):
        """Preview what the next sequence number will look like without consuming it."""
        padded_number = str(self.number_next).zfill(self.padding)
        return f"{self.prefix or ''}{padded_number}{self.suffix or ''}"

    @classmethod
    def next_by_code(cls, db: Session, code: str):
        """Get the next number for a sequence by its code."""
        env = Environment(db)
        sequence = env['sequence'].search([('code', '=', code), ('active', '=', True)], limit=1)
        if not sequence:
            raise UserError(f"No active sequence found with code '{code}'")
            
        return sequence.get_next_number()

    @classmethod
    def create_sequence(cls, db: Session, name: str, code: str, prefix: str = "", 
                       padding: int = 5, number_next: int = 1):
        """Helper method to create a new sequence."""
        return cls.create(db, {
            'name': name,
            'code': code,
            'prefix': prefix,
            'padding': padding,
            'number_next': number_next,
            'active': True
        })

    def reset_sequence(self, number_next: int = 1):
        """Reset the sequence to a specific number."""
        self.write({'number_next': number_next})

    @classmethod
    def get_sequence_info(cls, db: Session, code: str):
        """Get information about a sequence without consuming a number."""
        env = Environment(db)
        sequence = env['sequence'].search([('code', '=', code)], limit=1)
        if not sequence:
            return None
            
        return {
            'name': sequence.name,
            'code': sequence.code,
            'active': sequence.active,
            'next_number': sequence.number_next,
            'preview': sequence.preview_format()
        }

    def action_preview_next(self):
        """Action to preview the next sequence number"""
        self.ensure_one()
        preview = self.preview_format()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Next Sequence Number",
                "message": f"Next number will be: {preview}",
                "type": "info"
            }
        }

    def action_reset_sequence(self):
        """Action to reset sequence to 1"""
        self.ensure_one()
        old_next = self.number_next
        self.reset_sequence(1)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Sequence Reset",
                "message": f"Sequence reset from {old_next} to 1. Next number: {self.preview_format()}",
                "type": "success",
                "refresh": True
            }
        }
