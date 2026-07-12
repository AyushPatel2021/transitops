import os
from pathlib import Path

TEST_DB_PATH = Path("/tmp/znova1_backend_tests.db")

if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"
os.environ["LOAD_DEMO_DATA"] = "0"
