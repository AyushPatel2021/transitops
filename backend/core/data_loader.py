import os
import importlib.util
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.exc import DBAPIError, OperationalError, ProgrammingError, SQLAlchemyError
from sqlalchemy.orm import Session
from backend.core.base_model import Environment
from backend.core.database import SessionLocal, engine
from backend.services.auth_service import get_password_hash
from backend.core.registry import registry

logger = logging.getLogger(__name__)

class DataLoader:
    """
    Engine for loading structured data and demo records from Python files.
    Supports symbolic references (XML-IDs) and cross-file dependencies.
    """
    def __init__(self, db: Session):
        self.db = db
        self.env = Environment(db)
        self.xml_id_map: Dict[str, int] = {}  # xml_id -> database_id
        self._processed_files: List[str] = []

    def _reset_session(self):
        """Recreate the DB session after connection invalidation."""
        try:
            self.db.close()
        except Exception:
            pass

        try:
            engine.dispose()
        except Exception:
            pass

        self.db = SessionLocal()
        self.env = Environment(self.db)

    def _is_connection_error(self, error: Exception) -> bool:
        message = str(error).lower()
        if isinstance(error, (OperationalError, DBAPIError)):
            if getattr(error, "connection_invalidated", False):
                return True
        return (
            "can't reconnect until invalid transaction is rolled back" in message
            or "ssl connection has been closed unexpectedly" in message
            or "server closed the connection unexpectedly" in message
            or "connection refused" in message
        )

    def _format_error(self, error: Exception) -> str:
        message = str(error).strip()
        if "\n" in message:
            message = message.splitlines()[0].strip()
        return message

    def load_directory(self, directory_path: str):
        """Scan directory and load all .py files containing RECORDS"""
        if not os.path.exists(directory_path):
            logger.warning(f"Data directory not found: {directory_path}")
            return

        files = sorted([f for f in os.listdir(directory_path) if f.endswith('.py')])
        for file in files:
            file_path = os.path.join(directory_path, file)
            self.load_file(file_path)

    def load_file(self, file_path: str):
        """Load a single data file and process its RECORDS"""
        logger.info(f"Loading data from file: {file_path}")
        
        module_name = os.path.basename(file_path).replace('.py', '')
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if not spec or not spec.loader:
            logger.error(f"Could not load module spec for {file_path}")
            return

        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except Exception as e:
            logger.error(f"Error executing module {file_path}: {e}")
            return

        if not hasattr(module, 'RECORDS'):
            logger.debug(f"File {file_path} has no RECORDS dictionary, skipping.")
            return

        records = module.RECORDS
        self._process_records(records)
        self._processed_files.append(file_path)

    def _process_records(self, records: Dict[str, Any]):
        """Process a dictionary of records, resolving references and creating in DB"""
        # Sort records to ensure dependencies are met if defined in same file
        # This is a naive sort; complex dependencies across files might need multiple passes
        # or a better resolution strategy. For now, we'll try to process and retry if missing refs.
        
        pending_records = records.copy()
        max_retries = 3
        
        for attempt in range(max_retries):
            if not pending_records:
                break
                
            processed_this_turn = []
            for xml_id, definition in pending_records.items():
                try:
                    self._create_or_update_record(xml_id, definition)
                    self.db.commit()
                    processed_this_turn.append(xml_id)
                except ReferenceError:
                    # Reference not yet available, skip for now
                    continue
                except Exception as e:
                    self.db.rollback()
                    if self._is_connection_error(e):
                        logger.warning(f"Connection dropped while processing {xml_id}; resetting session and retrying once")
                        self._reset_session()
                        try:
                            self._create_or_update_record(xml_id, definition)
                            self.db.commit()
                            processed_this_turn.append(xml_id)
                            continue
                        except ReferenceError:
                            continue
                        except Exception as retry_error:
                            self.db.rollback()
                            logger.error(f"Failed to process record {xml_id}: {self._format_error(retry_error)}")
                            processed_this_turn.append(xml_id)
                            continue

                    logger.error(f"Failed to process record {xml_id}: {self._format_error(e)}")
                    # Remove to avoid infinite loop on fatal error
                    processed_this_turn.append(xml_id)
            
            for xml_id in processed_this_turn:
                del pending_records[xml_id]
                
        if pending_records:
            logger.error(f"Could not resolve references for some records after {max_retries} attempts: {list(pending_records.keys())}")

    def _create_or_update_record(self, xml_id: str, definition: Dict[str, Any]):
        """Creates or updates a single record based on its definition"""
        model_name = definition.get('model')
        vals = definition.get('values', {}).copy()
        noupdate = definition.get('noupdate', False)

        if not model_name:
            raise ValueError(f"Missing model name for record {xml_id}")

        model_cls = registry.get_model(model_name)
        if not model_cls:
            raise ValueError(f"Model '{model_name}' not found in registry for record {xml_id}")

        # Resolve references and magic prefixes
        processed_vals = self._resolve_values(vals)
        
        # Keep user_id when it is a real model field; otherwise do not confuse it
        # with the optional audit-tracking create argument.
        if 'user_id' not in getattr(model_cls, '_field_definitions', {}):
            processed_vals.pop('user_id', None)

        # Check for existing record by XML-ID (unique within the data loader session)
        # Note: In a production system, we'd store xml_ids in a dedicated 'ir_model_data' table.
        # For this implementation, we'll check by unique fields (like email for users, name for roles)
        # or just assume creation if it doesn't look like it's there.
        
        existing_record = self._find_existing_record(model_cls, processed_vals)
        
        record = None
        if existing_record:
            if not noupdate:
                logger.debug(f"Updating record {model_name}/{xml_id}")
                existing_record.write(processed_vals)
            else:
                logger.debug(f"Skipping update for record {model_name}/{xml_id} (noupdate=True)")
            self.xml_id_map[xml_id] = existing_record.id
            record = existing_record
        else:
            logger.info(f"Creating record {model_name}/{xml_id}")
            record = self.env[model_name].create(processed_vals)
            self.xml_id_map[xml_id] = record.id
            
        # Process method calls if any
        calls = definition.get('calls', [])
        for method_name in calls:
            method = getattr(record, method_name, None)
            if method:
                logger.info(f"Calling method {method_name} on {model_name}/{xml_id}")
                try:
                    method()
                except Exception as e:
                    logger.error(f"Error calling method {method_name} on {xml_id}: {e}")

    def _resolve_values(self, val: Any) -> Any:
        """Resolves symbolic references and magic prefixes in values recursively"""
        if isinstance(val, dict):
            return {k: self._resolve_values(v) for k, v in val.items()}
            
        elif isinstance(val, list):
            return [self._resolve_values(v) for v in val]
            
        elif isinstance(val, str):
            # Symbolic reference: @xml_id
            if val.startswith('@'):
                ref_id = val[1:]
                if ref_id in self.xml_id_map:
                    return self.xml_id_map[ref_id]
                else:
                    raise ReferenceError(f"Reference '{ref_id}' not yet loaded")
            
            # Magic prefix: $P$ for password hashing
            elif val.startswith('$P$'):
                raw_password = val[3:]
                return get_password_hash(raw_password)
            
            else:
                return val
        else:
            return val

    def _find_existing_record(self, model_cls, vals: Dict[str, Any]):
        """Try to find an existing record based on unique fields"""
        # Naive approach: search by specific fields for known models
        # In a real Znova, we'd use XML-IDs stored in DB.
        
        model_name = getattr(model_cls, '_model_name_', model_cls.__name__.lower())
        
        if model_name == 'role' and 'name' in vals:
            try:
                return self.env['role'].search([('name', '=', vals['name'])], limit=1)
            except (ProgrammingError, OperationalError, SQLAlchemyError):
                return None
        
        if model_name == 'user' and 'email' in vals:
            try:
                return self.env['user'].search([('email', '=', vals['email'])], limit=1)
            except (ProgrammingError, OperationalError, SQLAlchemyError):
                return None
            
        if model_name == 'sequence' and 'code' in vals:
            try:
                return self.env['sequence'].search([('code', '=', vals['code'])], limit=1)
            except (ProgrammingError, OperationalError, SQLAlchemyError):
                return None

        if model_name == 'cron' and 'code' in vals:
            try:
                return self.env['cron'].search([('code', '=', vals['code'])], limit=1)
            except (ProgrammingError, OperationalError, SQLAlchemyError):
                return None

        # Generic fallback for other models (like bcm.*)
        # Check if we can find by name/rec_name
        name_field = getattr(model_cls, '_name_field_', 'name')
        # Skip if name_field is complex (e.g. related field path) or not in vals
        if name_field and '.' not in name_field and name_field in vals:
            try:
                return self.env[model_name].search([(name_field, '=', vals[name_field])], limit=1)
            except (ProgrammingError, OperationalError, SQLAlchemyError):
                return None

        return None

def seed_data(db: Session, include_demo: bool = False):
    """Entry point for seeding data and optionally demo records"""
    loader = DataLoader(db)
    
    # Load core data
    logger.info("Seeding core data...")
    loader.load_directory('backend/data')
    
    # Load demo data if requested
    if include_demo:
        logger.info("Seeding demo data...")
        loader.load_directory('backend/demo')
