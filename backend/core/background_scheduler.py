"""
Background Task Scheduler

This module provides a background task scheduler for running periodic tasks
like notification cleanup, maintenance operations, and other background jobs.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
import traceback
from backend.core.database import SessionLocal
from backend.models.cron import Cron

logger = logging.getLogger(__name__)


@dataclass
class ScheduledTask:
    """Configuration for a scheduled background task"""
    name: str
    func: Callable
    interval_seconds: int
    run_immediately: bool = False
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None


class BackgroundScheduler:
    """
    Background task scheduler for periodic operations.
    
    Features:
    - Configurable task intervals
    - Error handling and retry logic
    - Task monitoring and statistics
    - Graceful shutdown
    - Async and sync task support
    """
    
    def __init__(self):
        """Initialize the background scheduler"""
        self.tasks: Dict[str, ScheduledTask] = {}
        self.running = False
        self.scheduler_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        
        logger.info("BackgroundScheduler initialized")
    
    def add_task(
        self,
        name: str,
        func: Callable,
        interval_seconds: int,
        run_immediately: bool = False,
        enabled: bool = True
    ) -> None:
        """
        Add a scheduled task.
        
        Args:
            name: Unique task name
            func: Function to execute (can be sync or async)
            interval_seconds: Interval between executions in seconds
            run_immediately: Whether to run the task immediately on startup
            enabled: Whether the task is enabled
        """
        if name in self.tasks:
            logger.warning(f"Task '{name}' already exists, replacing")
        
        now = datetime.utcnow()
        next_run = now if run_immediately else now + timedelta(seconds=interval_seconds)
        
        task = ScheduledTask(
            name=name,
            func=func,
            interval_seconds=interval_seconds,
            run_immediately=run_immediately,
            enabled=enabled,
            next_run=next_run
        )
        
        self.tasks[name] = task
        logger.info(f"Added scheduled task '{name}' with {interval_seconds}s interval")
    
    def remove_task(self, name: str) -> bool:
        """
        Remove a scheduled task.
        
        Args:
            name: Task name to remove
            
        Returns:
            True if task was removed, False if not found
        """
        if name in self.tasks:
            del self.tasks[name]
            logger.info(f"Removed scheduled task '{name}'")
            return True
        return False
    
    def enable_task(self, name: str) -> bool:
        """Enable a task"""
        if name in self.tasks:
            self.tasks[name].enabled = True
            logger.info(f"Enabled task '{name}'")
            return True
        return False
    
    def disable_task(self, name: str) -> bool:
        """Disable a task"""
        if name in self.tasks:
            self.tasks[name].enabled = False
            logger.info(f"Disabled task '{name}'")
            return True
        return False
    
    async def _execute_task(self, task: ScheduledTask) -> bool:
        """
        Execute a single task.
        
        Args:
            task: Task to execute
            
        Returns:
            True if successful, False if failed
        """
        try:
            logger.debug(f"Executing task '{task.name}'")
            start_time = datetime.utcnow()
            
            # Execute the task (handle both sync and async functions)
            if asyncio.iscoroutinefunction(task.func):
                result = await task.func()
            else:
                # Run sync function in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, task.func)
            
            # Update task statistics
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            task.last_run = start_time
            task.run_count += 1
            task.last_error = None
            
            # Schedule next run
            task.next_run = datetime.utcnow() + timedelta(seconds=task.interval_seconds)
            
            logger.info(f"Task '{task.name}' completed successfully in {execution_time:.2f}s")
            
            # Log result if it's a dict with useful info
            if isinstance(result, dict) and 'total_deleted' in result:
                logger.info(f"Task '{task.name}' result: {result}")
            
            return True
            
        except Exception as e:
            # Update error statistics
            task.error_count += 1
            task.last_error = str(e)
            
            # Schedule next run even after error
            task.next_run = datetime.utcnow() + timedelta(seconds=task.interval_seconds)
            
            logger.error(f"Task '{task.name}' failed: {e}")
            logger.debug(f"Task '{task.name}' traceback: {traceback.format_exc()}")
            
            return False
    
    async def _scheduler_loop(self) -> None:
        """Main scheduler loop"""
        logger.info("Background scheduler started")
        
        while self.running and not self._shutdown_event.is_set():
            try:
                now = datetime.utcnow()
                
                # Find tasks that need to run
                tasks_to_run = [
                    task for task in self.tasks.values()
                    if task.enabled and task.next_run and task.next_run <= now
                ]
                
                # Execute tasks
                for task in tasks_to_run:
                    if not self.running:
                        break
                    
                    await self._execute_task(task)
                
                # Wait before next check (check every 30 seconds)
                try:
                    await asyncio.wait_for(self._shutdown_event.wait(), timeout=30.0)
                    break  # Shutdown requested
                except asyncio.TimeoutError:
                    continue  # Normal timeout, continue loop
                    
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                logger.debug(f"Scheduler loop traceback: {traceback.format_exc()}")
                
                # Wait a bit before retrying
                try:
                    await asyncio.wait_for(self._shutdown_event.wait(), timeout=60.0)
                    break  # Shutdown requested
                except asyncio.TimeoutError:
                    continue  # Continue after error
        
        logger.info("Background scheduler stopped")
    
    async def start(self) -> None:
        """Start the background scheduler"""
        if self.running:
            logger.warning("Scheduler is already running")
            return
        
        self.running = True
        self._shutdown_event.clear()
        
        # Start the scheduler loop
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        
        logger.info(f"Background scheduler started with {len(self.tasks)} tasks")
    
    async def stop(self) -> None:
        """Stop the background scheduler"""
        if not self.running:
            return
        
        logger.info("Stopping background scheduler...")
        
        self.running = False
        self._shutdown_event.set()
        
        # Wait for scheduler task to complete
        if self.scheduler_task:
            try:
                await asyncio.wait_for(self.scheduler_task, timeout=10.0)
            except asyncio.TimeoutError:
                logger.warning("Scheduler task did not stop gracefully, cancelling")
                self.scheduler_task.cancel()
                try:
                    await self.scheduler_task
                except asyncio.CancelledError:
                    pass
        
        logger.info("Background scheduler stopped")
    
    def get_task_stats(self) -> Dict[str, Any]:
        """Get statistics for all tasks"""
        stats = {}
        
        for name, task in self.tasks.items():
            stats[name] = {
                'enabled': task.enabled,
                'interval_seconds': task.interval_seconds,
                'run_count': task.run_count,
                'error_count': task.error_count,
                'last_run': task.last_run.isoformat() if task.last_run else None,
                'next_run': task.next_run.isoformat() if task.next_run else None,
                'last_error': task.last_error
            }
        
        return {
            'running': self.running,
            'total_tasks': len(self.tasks),
            'enabled_tasks': sum(1 for t in self.tasks.values() if t.enabled),
            'tasks': stats
        }
    
    def get_task_status(self, name: str) -> Optional[Dict[str, Any]]:
        """Get status for a specific task"""
        if name not in self.tasks:
            return None
        
        task = self.tasks[name]
        return {
            'name': task.name,
            'enabled': task.enabled,
            'interval_seconds': task.interval_seconds,
            'run_count': task.run_count,
            'error_count': task.error_count,
            'last_run': task.last_run.isoformat() if task.last_run else None,
            'next_run': task.next_run.isoformat() if task.next_run else None,
            'last_error': task.last_error
        }


# Global scheduler instance
_scheduler: Optional[BackgroundScheduler] = None


def get_scheduler() -> BackgroundScheduler:
    """Get or create the global scheduler instance"""
    global _scheduler
    
    if _scheduler is None:
        _scheduler = BackgroundScheduler()
    
    return _scheduler


async def setup_notification_cleanup_task(
    interval_hours: int = 24,
    run_immediately: bool = False,
    cleanup_config: Optional[Dict[str, Any]] = None
) -> None:
    """
    Set up the notification cleanup background task.
    
    Args:
        interval_hours: Hours between cleanup runs
        run_immediately: Whether to run cleanup immediately on startup
        cleanup_config: Configuration for the cleanup service
    """
    from backend.services.notification_cleanup_service import (
        get_cleanup_service, 
        NotificationCleanupConfig
    )
    
    # Create cleanup service with config
    config = NotificationCleanupConfig(cleanup_config) if cleanup_config else None
    cleanup_service = get_cleanup_service(config)
    
    # Add task to scheduler
    scheduler = get_scheduler()
    scheduler.add_task(
        name="notification_cleanup",
        func=cleanup_service.run_cleanup,
        interval_seconds=interval_hours * 3600,  # Convert hours to seconds
        run_immediately=run_immediately,
        enabled=True
    )
    
    logger.info(f"Notification cleanup task scheduled to run every {interval_hours} hours")


async def setup_database_cron_task(
    interval_seconds: int = 60,
    run_immediately: bool = True
) -> None:
    """Set up the task that executes database-driven cron records."""
    def run_crons():
        db = SessionLocal()
        try:
            logger.debug("Checking for due database crons...")
            result = Cron.run_due_jobs(db)
            if result.get('executed', 0) > 0:
                logger.info(f"Executed {result['executed']} database crons")
            db.commit()
            return result
        except Exception as e:
            db.rollback()
            logger.error(f"Error running database crons: {e}")
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    scheduler = get_scheduler()
    scheduler.add_task(
        name="database_cron_runner",
        func=run_crons,
        interval_seconds=interval_seconds,
        run_immediately=run_immediately,
        enabled=True
    )

    logger.info(f"Database cron runner scheduled to run every {interval_seconds} seconds")


async def setup_default_background_tasks() -> None:
    """Set up default background tasks for the application"""
    
    # Set up notification cleanup (runs daily at startup, then every 24 hours)
    await setup_notification_cleanup_task(
        interval_hours=24,
        run_immediately=True,  # Run cleanup on startup
        cleanup_config={
            'read_retention_days': 30,      # Keep read notifications for 30 days
            'unread_retention_days': 90,    # Keep unread notifications for 90 days
            'expired_retention_days': 7,    # Keep expired notifications for 7 days after expiry
            'batch_size': 1000,             # Process 1000 notifications per batch
            'enable_vacuum': True,          # Run VACUUM after cleanup
            'vacuum_threshold': 1000,       # Run VACUUM if more than 1000 deleted
            'max_deletions_per_run': 10000, # Safety limit
            'detailed_logging': False       # Reduce log verbosity
        }
    )

    await setup_database_cron_task(
        interval_seconds=60,
        run_immediately=True
    )
    
    logger.info("Default background tasks configured")
