"""
TransientModel base class for wizard/popup forms.

TransientModel records are stored in the database but are temporary —
they are auto-cleaned after a configurable period (default: 1 hour).

Usage:
    class MyWizard(TransientModel):
        __tablename__ = "my_wizard"
        _model_name_ = "my.wizard"
        _description_ = "My Wizard"
        _transient_max_hours = 1  # Auto-cleanup after 1 hour (default)

        some_field = fields.Char(label="Some Field")

        def action_confirm(self):
            # Do something with the wizard data
            return {"type": "ir.actions.client", "tag": "close_wizard", "params": {"refresh": True}}
"""

from .znova_model import ZnovaModel


class TransientModel(ZnovaModel):
    """
    Base class for transient (wizard) models.
    
    Transient records are temporary and automatically cleaned up 
    after `_transient_max_hours` hours. They are used for popup wizards
    that collect data from the user and perform an action on confirm.
    
    Key differences from regular ZnovaModel:
    - `_transient = True` flag marks the model as transient
    - Records are auto-garbage-collected via cron
    - The frontend renders these as modal dialogs instead of full pages
    - Wizard records are deleted after the confirm action executes
    """
    __abstract__ = True
    
    # Framework flags
    _transient = True
    _transient_max_hours = 1  # Hours before auto-cleanup
    
    @classmethod
    def _gc_transient_records(cls, db=None):
        """
        Garbage-collect old transient records.
        Called by the cron system periodically.
        """
        from datetime import datetime, timedelta
        from backend.core.database import SessionLocal
        
        session = db or SessionLocal()
        own_session = db is None
        
        try:
            cutoff = datetime.utcnow() - timedelta(hours=cls._transient_max_hours)
            old_records = session.query(cls).filter(cls.created_at < cutoff).all()
            count = len(old_records)
            for record in old_records:
                session.delete(record)
            if own_session:
                session.commit()
            if count > 0:
                import logging
                logging.getLogger(__name__).info(
                    f"TransientModel GC: Cleaned {count} records from {cls.__tablename__}"
                )
            return count
        except Exception as e:
            if own_session:
                session.rollback()
            raise e
        finally:
            if own_session:
                session.close()
