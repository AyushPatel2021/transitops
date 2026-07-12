# Monkeypatch passlib for bcrypt compatibility
try:
    import bcrypt
    if not hasattr(bcrypt, '__about__'):
        bcrypt.__about__ = type('About', (), {'__version__': bcrypt.__version__})
except ImportError:
    pass

from contextlib import asynccontextmanager
import logging
import sys
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.core.database import engine, Base, SessionLocal
from backend.core.migration_manager import create_migration_manager
from backend.core.error_handler import setup_error_handlers
from backend.core.websocket_manager import get_websocket_manager
from backend.services.auth_service import get_password_hash
from backend.api.v1.endpoints import model_api, auth_api, profile_api, websocket_api, notification_api
from backend import models

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info("Starting Znova API...")
    
    # 1. Create tables first
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified/created")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        sys.exit(1)

    # 2. Run automatic database migrations
    try:
        migration_manager = create_migration_manager()
        
        # Validate migration environment
        if not migration_manager.validate_migration_environment():
            logger.error("Migration environment validation failed. Server startup aborted.")
            sys.exit(1)
        
        # Check if we need to stamp the database (if it's a fresh install from create_all)
        current_rev = migration_manager.get_current_revision()
        if current_rev is None:
            logger.info("Fresh database detected, stamping with head revision...")
            from alembic import command
            command.stamp(migration_manager.alembic_cfg, "head")
        
        # Check and apply migrations (including Zero-Touch)
        migration_result = await migration_manager.check_and_migrate()
        
        if not migration_result.success:
            logger.error(f"Database migration failed: {migration_result.error_message}")
            logger.error("Server startup aborted due to migration failure.")
            sys.exit(1)
        
        if migration_result.applied_migrations:
            logger.info(f"Applied migrations: {', '.join(migration_result.applied_migrations)}")
            logger.info(f"Migration completed in {migration_result.execution_time:.2f} seconds")
        
    except Exception as e:
        logger.error(f"Critical error during migration: {e}")
        logger.error("Server startup aborted.")
        sys.exit(1)
    
    # 3. Seed initial data (Roles, Admin, Sequences, Crons)
    from backend.core.data_loader import seed_data
    db = SessionLocal()
    try:
        load_demo = os.getenv("LOAD_DEMO_DATA", "0").lower() in ("1", "true", "yes")
        seed_data(db, include_demo=load_demo)
        logger.info("Data seeding and initialization completed successfully")
    except Exception as e:
        logger.error(f"Seeding error: {e}")
        db.rollback()
    finally:
        db.close()
    
    # Initialize WebSocket manager
    websocket_manager = get_websocket_manager()
    logger.info("WebSocket manager initialized")
    
    # 4. Start background task scheduler
    try:
        from backend.core.background_scheduler import get_scheduler, setup_default_background_tasks
        
        # Set up default background tasks (notification cleanup, etc.)
        await setup_default_background_tasks()
        
        # Start the scheduler
        scheduler = get_scheduler()
        await scheduler.start()
        
        logger.info("Background task scheduler started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start background scheduler: {e}")
        # Don't exit - scheduler is not critical for basic functionality
        logger.warning("Continuing without background scheduler")
    
    yield
    
    # Shutdown logic
    logger.info("Shutting down Znova API...")
    
    # Stop background scheduler
    try:
        from backend.core.background_scheduler import get_scheduler
        scheduler = get_scheduler()
        await scheduler.stop()
        logger.info("Background scheduler stopped")
    except Exception as e:
        logger.error(f"Error stopping background scheduler: {e}")

app = FastAPI(title="Znova API", lifespan=lifespan)

# Setup enhanced error handlers
setup_error_handlers(app)

# Add request logging middleware
@app.middleware("http")
async def log_requests(request, call_next):
    import time
    start_time = time.time()
    
    # Skip for WebSocket upgrade requests
    if request.headers.get("upgrade") == "websocket":
        return await call_next(request)
    
    response = await call_next(request)
    
    # Only log errors and slow requests (>1s)
    process_time = time.time() - start_time
    if response.status_code >= 400 or process_time > 1.0:
        logger.warning(f"{request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.3f}s")
    
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your actual domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# The standard CORSMiddleware handles CORS for HTTP.
# WebSockets usually don't need CORS middleware in FastAPI/Starlette
# but we ensure the Origin header is checked in the WebSocket endpoint if needed.

app.include_router(model_api.router, prefix="/api/v1/models", tags=["Models"])
app.include_router(auth_api.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(profile_api.router, prefix="/api/v1", tags=["Profile"])
app.include_router(websocket_api.router, prefix="/api/v1", tags=["WebSocket"])
app.include_router(notification_api.router, prefix="/api/v1", tags=["Notifications"])

@app.get("/")
def read_root():
    return {"message": "Welcome to Znova API"}

@app.get("/health/websocket")
def websocket_health():
    """Health check endpoint for WebSocket functionality"""
    websocket_manager = get_websocket_manager()
    stats = websocket_manager.get_connection_stats()
    return {
        "status": "healthy",
        "websocket_enabled": True,
        "active_connections": stats["total_connections"],
        "unique_users": stats["unique_users"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
