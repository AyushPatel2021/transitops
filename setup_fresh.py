import os
import sys
import subprocess
import time

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

# Now we can safely import these if we are in venv
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def setup_fresh_db():
    from sqlalchemy import create_engine, text
    from sqlalchemy.engine import url
    
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("Error: DATABASE_URL not found in .env")
        sys.exit(1)

    # Parse URL to get components
    u = url.make_url(DATABASE_URL)
    db_name = u.database
    # Create a URL for the 'postgres' database to perform administrative tasks
    admin_url = u.set(database="postgres")

    print(f"--- Setting up fresh database: {db_name} ---")
    
    engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        # Terminate other connections to the database
        print(f"Terminating existing connections to {db_name}...")
        conn.execute(text(f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{db_name}'
              AND pid <> pg_backend_pid();
        """))
        
        # Drop database if exists
        print(f"Dropping database {db_name} if it exists...")
        conn.execute(text(f"DROP DATABASE IF EXISTS {db_name}"))
        
        # Create database
        print(f"Creating database {db_name}...")
        conn.execute(text(f"CREATE DATABASE {db_name}"))

    print("--- Database recreated successfully ---")

def clean_migrations():
    """Remove all existing migration files"""
    print("--- Cleaning old migration files ---")
    versions_dir = os.path.join("backend", "migrations", "versions")
    if os.path.exists(versions_dir):
        for file in os.listdir(versions_dir):
            if file.endswith('.py') and not file.startswith('__'):
                file_path = os.path.join(versions_dir, file)
                os.remove(file_path)
                print(f"Removed: {file}")
    print("✓ Migration files cleaned")

def create_initial_migration():
    """Create fresh initial migration"""
    print("--- Creating initial migration ---")
    backend_dir = os.path.join(os.getcwd(), "backend")
    os.chdir(backend_dir)
    
    result = subprocess.run([
        sys.executable, "-m", "alembic", "revision",
        "--autogenerate", "-m", "initial_migration"
    ], check=False)
    
    os.chdir("..")
    
    if result.returncode == 0:
        print("✓ Initial migration created")
    else:
        print("⚠ Migration creation warning - will be handled by server")

def start_server():
    print("--- Starting Znova Backend Server ---")
    print("Migrations and seeding will run automatically via lifespan event.")
    
    python_exe = VENV_PYTHON if os.path.exists(VENV_PYTHON) else sys.executable
    print(f"Using python: {python_exe}")
    
    # Clean up ports before starting
    print("Clearing ports 8000 and 3000...")
    subprocess.run("fuser -k 8000/tcp 3000/tcp || true", shell=True)
    time.sleep(1)
    
    # Run uvicorn
    try:
        subprocess.run([
            python_exe, "-m", "uvicorn", 
            "backend.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ], check=True)
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Error starting server: {e}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Setup fresh database and migrations")
    parser.add_argument("--demo", action="store_true", help="Load demo data")
    args = parser.parse_args()

    if args.demo:
        os.environ["LOAD_DEMO_DATA"] = "1"
        print("--- Demo data loading ENABLED ---")

    try:
        setup_fresh_db()
        clean_migrations()
        create_initial_migration()
        start_server()
    except Exception as e:
        print(f"Critical Error: {e}")
        sys.exit(1)
