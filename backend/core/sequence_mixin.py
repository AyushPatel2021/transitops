import logging

from sqlalchemy.orm import object_session
from sqlalchemy.orm import Session

from backend.core.base_model import Environment
from backend.core.exceptions import UserError
from backend.models.sequence import Sequence

logger = logging.getLogger(__name__)

class SequenceMixin:
    """
    Mixin to add automatic sequence generation to any model.
    
    Usage:
        class Student(ZnovaModel, SequenceMixin):
            __tablename__ = "students"
            
            # Define the sequence field and code
            _sequence_field = "number"  # Field that will store the sequence
            _sequence_code = "student.student"  # Sequence code to use
            
            number = Column(String(50), default="New")
            name = Column(String(100))
    
    The mixin will automatically:
    1. Generate sequence numbers on create if the field contains "New"
    2. Handle the sequence generation in create_multi operations
    3. Provide helper methods for sequence management
    """
    
    # These should be defined in the inheriting class
    _sequence_field = None  # e.g., "number", "code", "reference"
    _sequence_code = None   # e.g., "student.student", "request.request"
    
    @classmethod
    def create(cls, db: Session, vals: dict):
        """
        Override create to handle sequence generation.
        Similar to the @api.model_create_multi pattern.
        """
        logger.info(f"SequenceMixin.create called for {cls.__name__} with vals: {vals}")
        
        # Check if sequence should be generated
        if (cls._sequence_field and cls._sequence_code and 
            cls._sequence_field in vals and 
            vals.get(cls._sequence_field) in (None, "", "New", "/")):
            
            logger.info(f"Generating sequence for field {cls._sequence_field} with code {cls._sequence_code}")
            
            try:
                sequence_number = Sequence.next_by_code(db, cls._sequence_code)
                logger.info(f"Generated sequence number: {sequence_number}")
                
                vals[cls._sequence_field] = sequence_number
                logger.info(f"Updated vals: {vals}")
                
            except UserError as e:
                logger.error(f"Failed to generate sequence for {cls.__name__}: {e}")
                # You can choose to raise the error or use a fallback
                raise e
        else:
            logger.info(f"No sequence generation needed. Field: {cls._sequence_field}, Code: {cls._sequence_code}, Field in vals: {cls._sequence_field in vals if cls._sequence_field else 'N/A'}, Field value: {vals.get(cls._sequence_field) if cls._sequence_field else 'N/A'}")
        
        logger.info(f"Calling super().create with vals: {vals}")
        result = super().create(db, vals)
        logger.info(f"Created record with ID: {result.id}, sequence field value: {getattr(result, cls._sequence_field) if cls._sequence_field else 'N/A'}")
        
        return result
    
    @classmethod
    def create_multi(cls, db: Session, vals_list: list):
        """
        Handle multiple record creation with sequence generation.
        Similar to the @api.model_create_multi decorator.
        """
        if not isinstance(vals_list, list):
            vals_list = [vals_list]
            
        # Process each record
        for vals in vals_list:
            # Check if sequence should be generated
            if (cls._sequence_field and cls._sequence_code and 
                cls._sequence_field in vals and 
                vals.get(cls._sequence_field) in (None, "", "New", "/")):
                
                try:
                    sequence_number = Sequence.next_by_code(db, cls._sequence_code)
                    vals[cls._sequence_field] = sequence_number
                    logger.info(f"Generated sequence {sequence_number} for {cls.__name__}")
                except UserError as e:
                    logger.error(f"Failed to generate sequence for {cls.__name__}: {e}")
                    raise e
        
        # Create all records
        created_records = []
        for vals in vals_list:
            record = super(SequenceMixin, cls).create(db, vals)
            created_records.append(record)
            
        return created_records
    
    def get_sequence_info(self, db: Session = None):
        """
        Get information about the sequence used by this model.
        
        Returns:
            dict: Sequence information or None if no sequence configured
        """
        if not self._sequence_code:
            return None
            
        if not db:
            db = object_session(self)
            
        if not db:
            return None
            
        return Sequence.get_sequence_info(db, self._sequence_code)
    
    @classmethod
    def ensure_sequence_exists(cls, db: Session, name: str = None, prefix: str = "", 
                              padding: int = 5, number_next: int = 1):
        """
        Ensure that the sequence for this model exists, create if not.
        
        Args:
            db: Database session
            name: Human-readable name (defaults to model name)
            prefix: Sequence prefix
            padding: Number padding
            number_next: Starting number
            
        Returns:
            Sequence: The sequence instance
        """
        if not cls._sequence_code:
            raise UserError(f"No sequence code defined for model {cls.__name__}")
            
        # Check if sequence exists
        env = Environment(db)
        sequence = env['sequence'].search([('code', '=', cls._sequence_code)], limit=1)
        
        if not sequence:
            # Create the sequence
            sequence_name = name or f"{cls.__name__} Sequence"
            sequence = env['sequence'].create({
                'name': sequence_name,
                'code': cls._sequence_code,
                'prefix': prefix,
                'padding': padding,
                'number_next': number_next,
                'active': True
            })
            logger.info(f"Created sequence '{cls._sequence_code}' for model {cls.__name__}")
        
        return sequence
    
    @classmethod
    def reset_sequence(cls, db: Session, number_next: int = 1):
        """
        Reset the sequence for this model to a specific number.
        
        Args:
            db: Database session
            number_next: Number to reset to
        """
        if not cls._sequence_code:
            raise UserError(f"No sequence code defined for model {cls.__name__}")
            
        env = Environment(db)
        sequence = env['sequence'].search([('code', '=', cls._sequence_code)], limit=1)
        if not sequence:
            raise UserError(f"Sequence '{cls._sequence_code}' not found")
            
        sequence.reset_sequence(number_next)
        logger.info(f"Reset sequence '{cls._sequence_code}' to {number_next}")


def sequence_field(field_name: str, sequence_code: str):
    """
    Decorator to easily add sequence functionality to a model.
    
    Usage:
        @sequence_field("number", "student.student")
        class Student(ZnovaModel):
            __tablename__ = "students"
            
            number = Column(String(50), default="New")
            name = Column(String(100))
    
    Args:
        field_name: Name of the field that will store the sequence
        sequence_code: Sequence code to use
        
    Returns:
        Decorated class with sequence functionality
    """
    def decorator(cls):
        # Add SequenceMixin to the class bases if not already present
        if SequenceMixin not in cls.__bases__:
            cls.__bases__ = (SequenceMixin,) + cls.__bases__
        
        # Set sequence configuration
        cls._sequence_field = field_name
        cls._sequence_code = sequence_code
        
        return cls
    
    return decorator


# Utility functions for sequence management

def create_sequence(db: Session, name: str, code: str, prefix: str = "", 
                   padding: int = 5, number_next: int = 1):
    """
    Utility function to create a sequence.
    
    Args:
        db: Database session
        name: Human-readable name
        code: Unique sequence code
        prefix: Sequence prefix
        padding: Number padding
        number_next: Starting number
        
    Returns:
        Sequence: Created sequence instance
    """
    return Sequence.create_sequence(db, name, code, prefix, padding, number_next)


def get_next_sequence(db: Session, code: str):
    """
    Utility function to get the next sequence number.
    
    Args:
        db: Database session
        code: Sequence code
        
    Returns:
        str: Next sequence number
    """
    return Sequence.next_by_code(db, code)


def sequence_exists(db: Session, code: str):
    """
    Check if a sequence exists.
    
    Args:
        db: Database session
        code: Sequence code
        
    Returns:
        bool: True if sequence exists
    """
    env = Environment(db)
    return env['sequence'].search([('code', '=', code)], limit=1).exists()
