from datetime import datetime, timedelta
from sqlalchemy.orm import Session, object_session
from backend.core.znova_model import ZnovaModel
from backend.core import fields
from backend.core.exceptions import ValidationError, UserError
from backend.core.base_model import Environment
from backend.core.registry import registry
import re
import importlib
import logging

logger = logging.getLogger(__name__)

class Cron(ZnovaModel):
    __tablename__ = "crons"
    _model_name_ = "cron"
    _name_field_ = "name"
    
    name = fields.Char(label="Cron Job Name", required=True, size=100, help="Human-readable name for this cron job")
    code = fields.Char(label="Cron Code", required=True, size=100, help="Unique code to identify this cron job")
    model_name = fields.Char(label="Model Name", required=True, size=100, help="Model class name where the function is defined (e.g., 'cron')")
    function_name = fields.Char(label="Function Name", required=True, size=100, help="Name of the function to call")
    
    interval_number = fields.Integer(label="Interval Number", default=1, help="How often to run")
    interval_type = fields.Selection([
        ("minutes", "Minutes"),
        ("hours", "Hours"),
        ("days", "Days"),
        ("weeks", "Weeks"),
        ("months", "Months")
    ], label="Interval Type", default="days", help="Time unit for the interval")
    
    next_call = fields.DateTime(label="Next Execution", help="When this cron job will run next")
    last_call = fields.DateTime(label="Last Execution", readonly=True, help="When this cron job last ran")
    active = fields.Boolean(label="Active", default=True, help="Whether this cron job is active")
    priority = fields.Integer(label="Priority", default=5, help="Priority level (1-10, lower number = higher priority)")
    description = fields.Text(label="Description", help="Description of what this cron job does")

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
            "read": False,
            "write": False,
            "delete": False,
            "domain": []
        }
    }


    _ui_views = {
        "form": {
            "groups": [
                {
                    "title": "Cron Job Information",
                    "fields": ["name", "code", "description", "active"]
                },
                {
                    "title": "Execution Configuration", 
                    "fields": ["model_name", "function_name", "priority"]
                },
                {
                    "title": "Schedule Configuration",
                    "fields": ["interval_number", "interval_type", "next_call", "last_call"]
                }
            ],
            "header_buttons": [
                {
                    "name": "run_now",
                    "label": "Run Now",
                    "type": "primary",
                    "method": "action_run_now"
                },
                {
                    "name": "reset_schedule",
                    "label": "Reset Schedule",
                    "type": "secondary",
                    "method": "action_reset_schedule"
                }
            ]
        },
        "list": {
            "fields": ["name", "code", "model_name", "function_name", "interval_number", "interval_type", "next_call", "active"],
            "search_fields": ["name", "code", "model_name", "function_name"]
        }
    }

    @classmethod
    def create(cls, db: Session, vals: dict):
        """Override create to validate cron configuration"""
        # Validate code format
        if 'code' in vals:
            code = vals['code']
            if not re.match(r'^[a-zA-Z0-9._-]+$', code):
                raise ValidationError("Cron code can only contain letters, numbers, dots, underscores and hyphens")
        
        # Validate interval
        if 'interval_number' in vals and vals['interval_number'] < 1:
            raise ValidationError("Interval number must be at least 1")
            
        # Validate priority
        if 'priority' in vals and (vals['priority'] < 1 or vals['priority'] > 10):
            raise ValidationError("Priority must be between 1 and 10")
            
        # Set default next_call if not provided
        if 'next_call' not in vals:
            vals['next_call'] = cls._calculate_next_call(
                vals.get('interval_number', 1),
                vals.get('interval_type', 'days')
            )
            
        return super().create(db, vals)

    def write(self, *args, **kwargs):
        """Override write to validate cron configuration"""
        if len(args) == 2 and isinstance(args[0], Session):
            db, vals = args
        elif len(args) == 1 and isinstance(args[0], dict):
            vals = args[0]
            db = object_session(self)
        else:
            vals = kwargs.get('vals', {})
            db = kwargs.get('db') or object_session(self)

        # Validate code format
        if 'code' in vals:
            code = vals['code']
            if not re.match(r'^[a-zA-Z0-9._-]+$', code):
                raise ValidationError("Cron code can only contain letters, numbers, dots, underscores and hyphens")
        
        # Validate interval
        if 'interval_number' in vals and vals['interval_number'] < 1:
            raise ValidationError("Interval number must be at least 1")
            
        # Validate priority
        if 'priority' in vals and (vals['priority'] < 1 or vals['priority'] > 10):
            raise ValidationError("Priority must be between 1 and 10")
            
        # Only recalculate next_call if interval changed AND next_call is not explicitly set
        if ('interval_number' in vals or 'interval_type' in vals) and 'next_call' not in vals:
            interval_number = vals.get('interval_number', self.interval_number)
            interval_type = vals.get('interval_type', self.interval_type)
            vals['next_call'] = self._calculate_next_call(interval_number, interval_type)
            
        return super().write(db, vals, **kwargs)

    @staticmethod
    def _calculate_next_call(interval_number: int, interval_type: str, base_time: datetime = None) -> datetime:
        """Calculate the next call time based on interval"""
        if base_time is None:
            base_time = datetime.now()
        
        if interval_type == "minutes":
            return base_time + timedelta(minutes=interval_number)
        elif interval_type == "hours":
            return base_time + timedelta(hours=interval_number)
        elif interval_type == "days":
            return base_time + timedelta(days=interval_number)
        elif interval_type == "weeks":
            return base_time + timedelta(weeks=interval_number)
        elif interval_type == "months":
            # Approximate months as 30 days
            return base_time + timedelta(days=interval_number * 30)
        else:
            return base_time + timedelta(days=1)

    def _calculate_future_next_call(self, execution_time: datetime) -> datetime:
        base_time = self.next_call if self.next_call and self.next_call > execution_time else execution_time
        return self._calculate_next_call(self.interval_number, self.interval_type, base_time)

    def execute(self, db: Session):
        """Execute the cron job by calling the specified function on the model."""
        if not self.active:
            raise UserError(f"Cron job '{self.code}' is not active")
            
        execution_time = datetime.now()
        try:
            # Import the model dynamically
            # For strict Znova, models are in backend.models.{model_name}
            # Or backend.models package.
            # Usually model_name provided is a dot-notated thing like 'module.class'
            # But here we might just store 'model_name' as the model identifier for registry?
            # The original code expected 'module.class'. 
            # Given we are simplifying, let's keep the logic but adapt if necessary.
            
            # Original logic:
            model_parts = self.model_name.split('.')
            if len(model_parts) != 2:
                # If strictly 2 parts required, we might have issues if we pass just 'cron'.
                # Let's see how it was used. Currently no active crons in default setup except what we create.
                # If we use strict registry lookups, we can just use registry.get_model(name).
                # But to maintain compatibility with existing logic, let's keep it.
                # Or even better, use registry!
                
                # Let's try registry first
                model_class = registry.get_model(self.model_name)
                
                if not model_class:
                     # Fallback to old dynamic import logic if registry fails or if name has dots
                     pass
            
            # Replicating original logic for safety as it was quite robust with fallbacks
            if len(model_parts) != 2:
                 # Try to load from registry if it's a simple name
                 model_class = registry.get_model(self.model_name)
                 if not model_class:
                     raise ValidationError(f"Invalid model name format: {self.model_name}. Expected format: 'module.model' or registry name")
            else:
                module_name, class_name = model_parts
                
                # Import the model class
                try:
                    module_path = f"backend.models.{module_name}"
                    module = importlib.import_module(module_path)
                    
                    # Try different class name variations
                    possible_class_names = [
                        class_name.title(),
                        class_name.capitalize(),
                        class_name.upper(),
                        class_name,
                    ]
                    
                    model_class = None
                    for possible_name in possible_class_names:
                        if hasattr(module, possible_name):
                            model_class = getattr(module, possible_name)
                            break
                    
                    if model_class is None:
                        # Fallback for old custom mappings
                         if module_name == "request":
                             if hasattr(module, "MaintenanceRequest"):
                                 model_class = getattr(module, "MaintenanceRequest")

                    if model_class is None:
                         raise ValidationError(f"Could not find model class for {self.model_name}")
                        
                except (ImportError, AttributeError) as e:
                    raise ValidationError(f"Could not import model {self.model_name}: {e}")
            
            # Check if the function exists on the model
            if not hasattr(model_class, self.function_name):
                raise ValidationError(f"Function '{self.function_name}' not found on model '{self.model_name}'")
            
            # Get the function
            func = getattr(model_class, self.function_name)
            
            # Execute the function
            logger.info(f"Executing cron job '{self.code}': {self.model_name}.{self.function_name}()")
            
            # Call the function - it should be a class method that accepts db session
            result = func(db)
            
            # Calculate next_call
            self.write(db, {
                'last_call': execution_time,
                'next_call': self._calculate_future_next_call(execution_time)
            })
            
            logger.info(f"Cron job '{self.code}' executed successfully")
            
            return {
                "success": True,
                "message": f"Cron job '{self.code}' executed successfully",
                "result": result
            }
            
        except Exception as e:
            execution_time = datetime.now()
            self.write(db, {
                'next_call': self._calculate_future_next_call(execution_time)
            })
            
            return {
                "success": False,
                "message": f"Error executing cron job '{self.code}': {str(e)}",
                "error": str(e)
            }

    @classmethod
    def get_due_jobs(cls, db: Session):
        now = datetime.now()
        env = Environment(db)
        return env['cron'].search([
            ('active', '=', True),
            ('next_call', '<=', now)
        ], order='priority asc, next_call asc')

    @staticmethod
    def run_transient_gc(db: Session):
        """
        Garbage-collect all transient models.
        Called by the 'transient_gc' cron job.
        """
        # Get all registered transient models
        transient_models = registry.get_transient_models()
        
        cleaned_count = 0
        cleaned_models = []
        
        for name, model_cls in transient_models.items():
            try:
                # Call GC on each model class
                count = model_cls._gc_transient_records(db)
                if count > 0:
                    cleaned_count += count
                    cleaned_models.append(f"{name} ({count})")
            except Exception as e:
                logger.error(f"Error cleaning transient model {name}: {e}")
                
        message = f"Cleaned {cleaned_count} transient records."
        if cleaned_models:
            message += f" Details: {', '.join(cleaned_models)}"
            
        return {
            "success": True, 
            "message": message,
            "result": {"cleaned_count": cleaned_count}
        }

    @classmethod
    def run_due_jobs(cls, db: Session):
        due_jobs = cls.get_due_jobs(db)
        
        if not due_jobs:
            return {"total": 0, "executed": 0, "failed": 0, "results": []}
        
        results = []
        executed = 0
        failed = 0
        
        for job in due_jobs:
            try:
                result = job.execute(db)
                results.append({"code": job.code, "name": job.name, **result})
                
                if result["success"]:
                    executed += 1
                else:
                    failed += 1
                    
            except Exception as e:
                logger.error(f"Unexpected error running cron job '{job.code}': {e}")
                results.append({
                    "code": job.code,
                    "name": job.name,
                    "success": False,
                    "message": f"Unexpected error: {str(e)}",
                    "error": str(e)
                })
                failed += 1
        
        return {"total": len(due_jobs), "executed": executed, "failed": failed, "results": results}

    def action_run_now(self):
        db = object_session(self)
        if db:
            result = self.execute(db)
            if result["success"]:
                return {
                    "type": "ir.actions.client",
                    "tag": "display_notification",
                    "params": {
                        "title": "Cron Job Executed",
                        "message": result["message"],
                        "type": "success",
                        "refresh": True
                    }
                }
            else:
                 return {
                    "type": "ir.actions.client",
                    "tag": "display_notification",
                    "params": {
                        "title": "Execution Failed",
                        "message": result["message"],
                        "type": "error"
                    }
                }
        return {"type": "error", "message": "No database session"}

    def action_reset_schedule(self):
        db = object_session(self)
        if db:
            old_next = self.next_call
            self.next_call = self._calculate_next_call(self.interval_number, self.interval_type)
            db.commit()
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Schedule Reset",
                    "message": f"Next execution reset from {old_next} to {self.next_call}",
                    "type": "success",
                    "refresh": True
                }
            }
        return {"type": "error", "message": "No database session"}
