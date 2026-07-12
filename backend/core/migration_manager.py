"""
Migration Manager for automatic database schema synchronization.

This module provides automatic database migration capabilities that integrate
with FastAPI startup to ensure database schema is always up-to-date.
"""

import os
import sys
import logging
from typing import List, Optional
from dataclasses import dataclass
from pathlib import Path
import time

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


@dataclass
class MigrationResult:
    """Result of a migration operation."""
    success: bool
    applied_migrations: List[str]
    error_message: Optional[str]
    execution_time: float


class MigrationManager:
    """
    Manages automatic database migrations using Alembic.
    
    This class provides programmatic access to Alembic migration operations
    and integrates with FastAPI startup to ensure database schema is synchronized.
    """
    
    def __init__(self, alembic_config_path: str, database_url: str):
        """
        Initialize the migration manager.
        
        Args:
            alembic_config_path: Path to the alembic.ini configuration file
            database_url: Database connection URL
        """
        self.alembic_config_path = alembic_config_path
        self.database_url = database_url
        self.engine = create_engine(database_url)
        
        # Setup Alembic configuration
        self.alembic_cfg = Config(alembic_config_path)
        self.alembic_cfg.set_main_option("sqlalchemy.url", database_url)
        
        # Get script directory
        self.script_dir = ScriptDirectory.from_config(self.alembic_cfg)
    
    def get_current_revision(self) -> Optional[str]:
        """
        Get the current database revision.
        
        Returns:
            Current revision ID or None if no migrations have been applied
        """
        try:
            with self.engine.connect() as connection:
                context = MigrationContext.configure(connection)
                return context.get_current_revision()
        except Exception as e:
            logger.error(f"Failed to get current revision: {e}")
            return None
    
    def get_pending_migrations(self) -> List[str]:
        """
        Get list of pending migrations that need to be applied.
        
        Returns:
            List of revision IDs that need to be applied
        """
        try:
            current_rev = self.get_current_revision()
            head_rev = self.script_dir.get_current_head()
            
            if current_rev == head_rev:
                return []
            
            # Get all revisions from current to head
            if current_rev is None:
                # No migrations applied yet, get all revisions
                revisions = list(self.script_dir.walk_revisions())
                return [rev.revision for rev in reversed(revisions)]
            else:
                # Get revisions between current and head
                revisions = list(self.script_dir.walk_revisions(current_rev, head_rev))
                return [rev.revision for rev in reversed(revisions) if rev.revision != current_rev]
                
        except Exception as e:
            logger.error(f"Failed to get pending migrations: {e}")
            return []
    
    def has_schema_changes(self) -> bool:
        """
        Check if there are pending schema changes.
        
        Returns:
            True if there are pending migrations, False otherwise
        """
        pending = self.get_pending_migrations()
        return len(pending) > 0
    
    def apply_migrations(self) -> MigrationResult:
        """
        Apply all pending migrations.
        
        Returns:
            MigrationResult with details of the operation
        """
        start_time = time.time()
        
        try:
            pending_migrations = self.get_pending_migrations()
            
            if not pending_migrations:
                logger.info("No pending migrations to apply")
                return MigrationResult(
                    success=True,
                    applied_migrations=[],
                    error_message=None,
                    execution_time=time.time() - start_time
                )
            
            logger.info(f"Applying {len(pending_migrations)} pending migrations: {pending_migrations}")
            
            # Apply migrations using Alembic command
            command.upgrade(self.alembic_cfg, "head")
            
            execution_time = time.time() - start_time
            logger.info(f"Successfully applied {len(pending_migrations)} migrations in {execution_time:.2f}s")
            
            return MigrationResult(
                success=True,
                applied_migrations=pending_migrations,
                error_message=None,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Migration failed: {str(e)}"
            logger.error(error_msg)
            
            return MigrationResult(
                success=False,
                applied_migrations=[],
                error_message=error_msg,
                execution_time=execution_time
            )
    
    async def check_and_migrate(self) -> MigrationResult:
        """
        Check for schema changes and apply migrations if needed.
        
        This is the main method called during FastAPI startup.
        """
        logger.info("Checking for database schema changes...")
        
        try:
            # Test database connection first
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            # 1. First apply any standard Alembic migrations
            if self.has_schema_changes():
                logger.info("Alembic migrations detected, applying...")
                result = self.apply_migrations()
                if not result.success:
                    return result
            
            # 2. Apply Zero-Touch migrations (missing columns)
            logger.info("Syncing dynamic schema changes (Zero-Touch)...")
            self._apply_zero_touch_migrations()
            
            logger.info("Database schema is up-to-date")
            return MigrationResult(
                success=True,
                applied_migrations=[],
                error_message=None,
                execution_time=0.0
            )
                
        except Exception as e:
            error_msg = f"Database migration check failed: {str(e)}"
            logger.error(error_msg)
            return MigrationResult(
                success=False,
                applied_migrations=[],
                error_message=error_msg,
                execution_time=0.0
            )

    def _apply_zero_touch_migrations(self):
        """
        Scan all registered models and add missing columns to the database.
        This provides a 'zero-touch' experience for extending models.
        """
        from backend.core.registry import registry
        from sqlalchemy import inspect
        
        inspector = inspect(self.engine)
        
        for model_name, model_cls in registry._models.items():
            # Skip abstract models (they don't have actual tables)
            if getattr(model_cls, '__abstract__', False) or not hasattr(model_cls, '__tablename__') or model_cls.__tablename__ is None:
                logger.debug(f"Skipping abstract model: {model_name}")
                continue
                
            table_name = model_cls.__tablename__
            
            # Get existing columns in DB
            try:
                existing_columns = {col['name'] for col in inspector.get_columns(table_name)}
            except Exception as e:
                logger.error(f"Could not inspect table {table_name}: {e}")
                continue
            
            # Check for missing columns in model
            for column in model_cls.__table__.columns:
                if column.name not in existing_columns:
                    logger.info(f"Detected missing column {column.name} in table {table_name}. Adding...")
                    
                    # Generate ALTER TABLE command
                    column_type = column.type.compile(self.engine.dialect)
                    nullable = "NULL" if column.nullable else "NOT NULL"
                    default = ""
                    if column.server_default:
                        # This is a bit complex to generalize perfectly, but for simple defaults:
                        default = f" DEFAULT {column.server_default.arg.text}"
                    
                    alter_cmd = f'ALTER TABLE "{table_name}" ADD COLUMN "{column.name}" {column_type} {nullable} {default}'
                    
                    try:
                        with self.engine.connect() as conn:
                            conn.execute(text(alter_cmd))
                            conn.commit()
                        logger.info(f"Successfully added column {column.name} to {table_name}")
                    except Exception as e:
                        logger.error(f"Failed to add column {column.name} to {table_name}: {e}")
    
    def validate_migration_environment(self) -> bool:
        """
        Validate that the migration environment is properly configured.
        
        Returns:
            True if environment is valid, False otherwise
        """
        try:
            # Check if alembic.ini exists
            if not os.path.exists(self.alembic_config_path):
                logger.error(f"Alembic configuration file not found: {self.alembic_config_path}")
                return False
            
            # Check if migrations directory exists
            script_location = self.alembic_cfg.get_main_option("script_location")
            if not os.path.exists(script_location):
                logger.error(f"Migrations directory not found: {script_location}")
                return False
            
            # Test database connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            logger.info("Migration environment validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Migration environment validation failed: {e}")
            return False


def create_migration_manager(database_url: str = None) -> MigrationManager:
    """
    Factory function to create a MigrationManager instance.
    
    Args:
        database_url: Database URL, if None will use environment variable
        
    Returns:
        Configured MigrationManager instance
    """
    if database_url is None:
        from backend.core.database import DATABASE_URL
        database_url = DATABASE_URL
    
    # Get the path to alembic.ini relative to this file
    backend_dir = Path(__file__).parent.parent
    alembic_config_path = backend_dir / "alembic.ini"
    
    return MigrationManager(str(alembic_config_path), database_url)