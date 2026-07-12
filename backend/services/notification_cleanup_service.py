"""
Notification Cleanup Service

This service handles the background cleanup of expired and old notifications
with configurable retention policies and optimized database operations.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text
from backend.models.notification import Notification
from backend.core.database import SessionLocal
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class NotificationCleanupConfig:
    """Configuration for notification cleanup policies"""
    
    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        """
        Initialize cleanup configuration.
        
        Args:
            config_dict: Configuration dictionary with cleanup settings
        """
        config = config_dict or {}
        
        # Default retention policies (in days)
        self.read_retention_days = config.get('read_retention_days', 30)
        self.unread_retention_days = config.get('unread_retention_days', 90)
        self.expired_retention_days = config.get('expired_retention_days', 7)
        
        # Batch processing settings
        self.batch_size = config.get('batch_size', 1000)
        self.max_batches_per_run = config.get('max_batches_per_run', 10)
        
        # Performance settings
        self.enable_vacuum = config.get('enable_vacuum', True)
        self.vacuum_threshold = config.get('vacuum_threshold', 5000)  # Min deletions to trigger vacuum
        
        # Safety settings
        self.max_deletions_per_run = config.get('max_deletions_per_run', 50000)
        self.dry_run = config.get('dry_run', False)
        
        # Logging settings
        self.log_level = config.get('log_level', 'INFO')
        self.detailed_logging = config.get('detailed_logging', False)
    
    def validate(self) -> bool:
        """Validate configuration values"""
        if self.read_retention_days < 1:
            logger.error("read_retention_days must be at least 1")
            return False
        
        if self.unread_retention_days < self.read_retention_days:
            logger.error("unread_retention_days must be >= read_retention_days")
            return False
        
        if self.batch_size < 100 or self.batch_size > 10000:
            logger.error("batch_size must be between 100 and 10000")
            return False
        
        if self.max_deletions_per_run < 1000:
            logger.error("max_deletions_per_run must be at least 1000")
            return False
        
        return True


class NotificationCleanupService:
    """
    Background service for cleaning up expired and old notifications.
    
    Features:
    - Configurable retention policies for read/unread notifications
    - Batch processing for large datasets
    - Database optimization with VACUUM
    - Safety limits and dry-run mode
    - Detailed logging and monitoring
    """
    
    def __init__(self, config: Optional[NotificationCleanupConfig] = None):
        """
        Initialize cleanup service.
        
        Args:
            config: Cleanup configuration (uses defaults if None)
        """
        self.config = config or NotificationCleanupConfig()
        
        if not self.config.validate():
            raise ValueError("Invalid cleanup configuration")
        
        # Set up logging level
        if self.config.log_level == 'DEBUG':
            logger.setLevel(logging.DEBUG)
        elif self.config.log_level == 'WARNING':
            logger.setLevel(logging.WARNING)
        
        # Thread pool for async operations
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="cleanup")
        
        logger.info(f"NotificationCleanupService initialized with config: "
                   f"read_retention={self.config.read_retention_days}d, "
                   f"unread_retention={self.config.unread_retention_days}d, "
                   f"batch_size={self.config.batch_size}")
    
    def _get_cleanup_cutoff_dates(self) -> Dict[str, datetime]:
        """Calculate cutoff dates for different cleanup categories"""
        now = datetime.utcnow()
        
        return {
            'read_cutoff': now - timedelta(days=self.config.read_retention_days),
            'unread_cutoff': now - timedelta(days=self.config.unread_retention_days),
            'expired_cutoff': now - timedelta(days=self.config.expired_retention_days)
        }
    
    def _count_notifications_to_cleanup(self, db: Session) -> Dict[str, int]:
        """Count notifications that would be cleaned up"""
        cutoffs = self._get_cleanup_cutoff_dates()
        
        # Count expired notifications (past their expires_at date + grace period)
        expired_count = db.query(func.count(Notification.id)).filter(
            and_(
                Notification.expires_at.isnot(None),
                Notification.expires_at < cutoffs['expired_cutoff']
            )
        ).scalar() or 0
        
        # Count old read notifications
        read_count = db.query(func.count(Notification.id)).filter(
            and_(
                Notification.read == True,
                Notification.created_at < cutoffs['read_cutoff'],
                or_(
                    Notification.expires_at.is_(None),
                    Notification.expires_at >= cutoffs['expired_cutoff']
                )
            )
        ).scalar() or 0
        
        # Count very old unread notifications
        unread_count = db.query(func.count(Notification.id)).filter(
            and_(
                Notification.read == False,
                Notification.created_at < cutoffs['unread_cutoff'],
                or_(
                    Notification.expires_at.is_(None),
                    Notification.expires_at >= cutoffs['expired_cutoff']
                )
            )
        ).scalar() or 0
        
        return {
            'expired': expired_count,
            'read': read_count,
            'unread': unread_count,
            'total': expired_count + read_count + unread_count
        }
    
    def _cleanup_expired_notifications(self, db: Session) -> int:
        """Clean up notifications that have passed their expiration date"""
        cutoffs = self._get_cleanup_cutoff_dates()
        
        if self.config.dry_run:
            count = db.query(func.count(Notification.id)).filter(
                and_(
                    Notification.expires_at.isnot(None),
                    Notification.expires_at < cutoffs['expired_cutoff']
                )
            ).scalar() or 0
            logger.info(f"[DRY RUN] Would delete {count} expired notifications")
            return count
        
        # Delete in batches
        total_deleted = 0
        batch_count = 0
        
        while batch_count < self.config.max_batches_per_run:
            # Get batch of IDs to delete
            batch_ids = db.query(Notification.id).filter(
                and_(
                    Notification.expires_at.isnot(None),
                    Notification.expires_at < cutoffs['expired_cutoff']
                )
            ).limit(self.config.batch_size).all()
            
            if not batch_ids:
                break
            
            # Delete batch
            ids_to_delete = [row.id for row in batch_ids]
            deleted_count = db.query(Notification).filter(
                Notification.id.in_(ids_to_delete)
            ).delete(synchronize_session=False)
            
            db.commit()
            total_deleted += deleted_count
            batch_count += 1
            
            if self.config.detailed_logging:
                logger.debug(f"Deleted batch {batch_count}: {deleted_count} expired notifications")
            
            # Safety check
            if total_deleted >= self.config.max_deletions_per_run:
                logger.warning(f"Reached max deletions limit ({self.config.max_deletions_per_run}), stopping")
                break
        
        if total_deleted > 0:
            logger.info(f"Deleted {total_deleted} expired notifications in {batch_count} batches")
        
        return total_deleted
    
    def _cleanup_old_read_notifications(self, db: Session) -> int:
        """Clean up old read notifications"""
        cutoffs = self._get_cleanup_cutoff_dates()
        
        if self.config.dry_run:
            count = db.query(func.count(Notification.id)).filter(
                and_(
                    Notification.read == True,
                    Notification.created_at < cutoffs['read_cutoff'],
                    or_(
                        Notification.expires_at.is_(None),
                        Notification.expires_at >= cutoffs['expired_cutoff']
                    )
                )
            ).scalar() or 0
            logger.info(f"[DRY RUN] Would delete {count} old read notifications")
            return count
        
        # Delete in batches
        total_deleted = 0
        batch_count = 0
        
        while batch_count < self.config.max_batches_per_run:
            # Get batch of IDs to delete
            batch_ids = db.query(Notification.id).filter(
                and_(
                    Notification.read == True,
                    Notification.created_at < cutoffs['read_cutoff'],
                    or_(
                        Notification.expires_at.is_(None),
                        Notification.expires_at >= cutoffs['expired_cutoff']
                    )
                )
            ).limit(self.config.batch_size).all()
            
            if not batch_ids:
                break
            
            # Delete batch
            ids_to_delete = [row.id for row in batch_ids]
            deleted_count = db.query(Notification).filter(
                Notification.id.in_(ids_to_delete)
            ).delete(synchronize_session=False)
            
            db.commit()
            total_deleted += deleted_count
            batch_count += 1
            
            if self.config.detailed_logging:
                logger.debug(f"Deleted batch {batch_count}: {deleted_count} old read notifications")
            
            # Safety check
            if total_deleted >= self.config.max_deletions_per_run:
                logger.warning(f"Reached max deletions limit ({self.config.max_deletions_per_run}), stopping")
                break
        
        if total_deleted > 0:
            logger.info(f"Deleted {total_deleted} old read notifications in {batch_count} batches")
        
        return total_deleted
    
    def _cleanup_very_old_unread_notifications(self, db: Session) -> int:
        """Clean up very old unread notifications"""
        cutoffs = self._get_cleanup_cutoff_dates()
        
        if self.config.dry_run:
            count = db.query(func.count(Notification.id)).filter(
                and_(
                    Notification.read == False,
                    Notification.created_at < cutoffs['unread_cutoff'],
                    or_(
                        Notification.expires_at.is_(None),
                        Notification.expires_at >= cutoffs['expired_cutoff']
                    )
                )
            ).scalar() or 0
            logger.info(f"[DRY RUN] Would delete {count} very old unread notifications")
            return count
        
        # Delete in batches
        total_deleted = 0
        batch_count = 0
        
        while batch_count < self.config.max_batches_per_run:
            # Get batch of IDs to delete
            batch_ids = db.query(Notification.id).filter(
                and_(
                    Notification.read == False,
                    Notification.created_at < cutoffs['unread_cutoff'],
                    or_(
                        Notification.expires_at.is_(None),
                        Notification.expires_at >= cutoffs['expired_cutoff']
                    )
                )
            ).limit(self.config.batch_size).all()
            
            if not batch_ids:
                break
            
            # Delete batch
            ids_to_delete = [row.id for row in batch_ids]
            deleted_count = db.query(Notification).filter(
                Notification.id.in_(ids_to_delete)
            ).delete(synchronize_session=False)
            
            db.commit()
            total_deleted += deleted_count
            batch_count += 1
            
            if self.config.detailed_logging:
                logger.debug(f"Deleted batch {batch_count}: {deleted_count} very old unread notifications")
            
            # Safety check
            if total_deleted >= self.config.max_deletions_per_run:
                logger.warning(f"Reached max deletions limit ({self.config.max_deletions_per_run}), stopping")
                break
        
        if total_deleted > 0:
            logger.info(f"Deleted {total_deleted} very old unread notifications in {batch_count} batches")
        
        return total_deleted
    
    def _optimize_database(self, db: Session, total_deleted: int) -> bool:
        """Optimize database after cleanup operations"""
        if not self.config.enable_vacuum or total_deleted < self.config.vacuum_threshold:
            return False
        
        if self.config.dry_run:
            logger.info(f"[DRY RUN] Would run VACUUM on notifications table")
            return True
        
        try:
            # Run VACUUM on notifications table to reclaim space
            logger.info(f"Running VACUUM on notifications table after deleting {total_deleted} records")
            
            # Use raw SQL for VACUUM (can't be run in transaction)
            db.commit()  # Ensure no active transaction
            db.execute(text("VACUUM notifications"))
            
            logger.info("VACUUM completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to run VACUUM: {e}")
            return False
    
    def run_cleanup(self) -> Dict[str, Any]:
        """
        Run the complete cleanup process.
        
        Returns:
            Dictionary with cleanup results and statistics
        """
        start_time = datetime.utcnow()
        logger.info("Starting notification cleanup process")
        
        db = SessionLocal()
        try:
            # Get initial counts
            initial_counts = self._count_notifications_to_cleanup(db)
            
            if initial_counts['total'] == 0:
                logger.info("No notifications to clean up")
                return {
                    'success': True,
                    'total_deleted': 0,
                    'categories': {'expired': 0, 'read': 0, 'unread': 0},
                    'execution_time': 0,
                    'vacuum_run': False,
                    'dry_run': self.config.dry_run
                }
            
            logger.info(f"Found {initial_counts['total']} notifications to clean up: "
                       f"expired={initial_counts['expired']}, "
                       f"read={initial_counts['read']}, "
                       f"unread={initial_counts['unread']}")
            
            # Run cleanup operations
            deleted_counts = {
                'expired': self._cleanup_expired_notifications(db),
                'read': self._cleanup_old_read_notifications(db),
                'unread': self._cleanup_very_old_unread_notifications(db)
            }
            
            total_deleted = sum(deleted_counts.values())
            
            # Optimize database if needed
            vacuum_run = self._optimize_database(db, total_deleted)
            
            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            result = {
                'success': True,
                'total_deleted': total_deleted,
                'categories': deleted_counts,
                'execution_time': execution_time,
                'vacuum_run': vacuum_run,
                'dry_run': self.config.dry_run
            }
            
            if self.config.dry_run:
                logger.info(f"[DRY RUN] Cleanup completed in {execution_time:.2f}s - "
                           f"would delete {total_deleted} notifications")
            else:
                logger.info(f"Cleanup completed in {execution_time:.2f}s - "
                           f"deleted {total_deleted} notifications")
            
            return result
            
        except Exception as e:
            logger.error(f"Cleanup process failed: {e}")
            db.rollback()
            return {
                'success': False,
                'error': str(e),
                'total_deleted': 0,
                'categories': {'expired': 0, 'read': 0, 'unread': 0},
                'execution_time': (datetime.utcnow() - start_time).total_seconds(),
                'vacuum_run': False,
                'dry_run': self.config.dry_run
            }
        finally:
            db.close()
    
    async def run_cleanup_async(self) -> Dict[str, Any]:
        """
        Run cleanup process asynchronously.
        
        Returns:
            Dictionary with cleanup results and statistics
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self.run_cleanup)
    
    def get_cleanup_stats(self) -> Dict[str, Any]:
        """
        Get statistics about notifications that would be cleaned up.
        
        Returns:
            Dictionary with cleanup statistics
        """
        db = SessionLocal()
        try:
            counts = self._count_notifications_to_cleanup(db)
            cutoffs = self._get_cleanup_cutoff_dates()
            
            return {
                'counts': counts,
                'cutoff_dates': {
                    'read_cutoff': cutoffs['read_cutoff'].isoformat(),
                    'unread_cutoff': cutoffs['unread_cutoff'].isoformat(),
                    'expired_cutoff': cutoffs['expired_cutoff'].isoformat()
                },
                'config': {
                    'read_retention_days': self.config.read_retention_days,
                    'unread_retention_days': self.config.unread_retention_days,
                    'expired_retention_days': self.config.expired_retention_days,
                    'batch_size': self.config.batch_size
                }
            }
        finally:
            db.close()
    
    def shutdown(self):
        """Shutdown the cleanup service and cleanup resources"""
        logger.info("Shutting down NotificationCleanupService")
        self.executor.shutdown(wait=True)


# Global cleanup service instance
_cleanup_service: Optional[NotificationCleanupService] = None


def get_cleanup_service(config: Optional[NotificationCleanupConfig] = None) -> NotificationCleanupService:
    """
    Get or create the global cleanup service instance.
    
    Args:
        config: Cleanup configuration (only used on first call)
        
    Returns:
        NotificationCleanupService instance
    """
    global _cleanup_service
    
    if _cleanup_service is None:
        _cleanup_service = NotificationCleanupService(config)
    
    return _cleanup_service


def create_cleanup_service(config: Optional[NotificationCleanupConfig] = None) -> NotificationCleanupService:
    """
    Create a new cleanup service instance (for testing or custom configurations).
    
    Args:
        config: Cleanup configuration
        
    Returns:
        New NotificationCleanupService instance
    """
    return NotificationCleanupService(config)