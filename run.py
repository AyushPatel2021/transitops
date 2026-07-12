import os
import sys
import subprocess

# Try to find the python executable in venv
VENV_PYTHON = os.path.join(os.getcwd(), "backend", "venv", "bin", "python")
if not os.path.exists(VENV_PYTHON):
    VENV_PYTHON = os.path.join(os.getcwd(), "venv", "bin", "python")

def restart_with_venv():
    if os.path.exists(VENV_PYTHON) and sys.executable != VENV_PYTHON:
        if os.environ.get("RESTARTED_WITH_VENV") != "1":
            print(f"Restarting with venv python: {VENV_PYTHON}")
            env = os.environ.copy()
            env["RESTARTED_WITH_VENV"] = "1"
            os.execv(VENV_PYTHON, [VENV_PYTHON] + sys.argv)

# Initial restart check
restart_with_venv()

def run_migrations():
    """Initialize and run database migrations"""
    print("--- Checking Database Migrations ---")
    
    backend_dir = os.path.join(os.getcwd(), "backend")
    migrations_dir = os.path.join(backend_dir, "migrations")
    versions_dir = os.path.join(migrations_dir, "versions")
    
    # Check if migrations directory exists
    if not os.path.exists(migrations_dir):
        print("Initializing Alembic migrations...")
        os.chdir(backend_dir)
        subprocess.run([sys.executable, "-m", "alembic", "init", "migrations"], check=True)
        os.chdir("..")
    
    # Check if any migration files exist
    migration_files = [f for f in os.listdir(versions_dir) if f.endswith('.py') and not f.startswith('__')]
    
    if not migration_files:
        print("No migration files found. Creating initial migration...")
        os.chdir(backend_dir)
        subprocess.run([
            sys.executable, "-m", "alembic", "revision", 
            "--autogenerate", "-m", "initial_migration"
        ], check=True)
        os.chdir("..")
    
    # Apply migrations
    print("Applying database migrations...")
    os.chdir(backend_dir)
    result = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=False)
    os.chdir("..")
    
    if result.returncode == 0:
        print("✓ Migrations applied successfully")
    else:
        print("⚠ Migration warning - will be handled by server startup")
    
    return result.returncode == 0

def start_server():
    # Load environment variables if possible
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    print("--- Starting Znova Backend Server ---")
    print(f"Using python: {sys.executable}")
    
    # Run migrations first
    run_migrations()
    
    print("\n--- Starting FastAPI Server ---")
    
    # Run uvicorn directly for better logging visibility
    try:
        import uvicorn
        uvicorn.run(
            "backend.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Error starting server: {e}")

if __name__ == "__main__":
    start_server()
