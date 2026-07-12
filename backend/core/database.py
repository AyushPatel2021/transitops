import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, scoped_session
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:password@localhost:5432/enterprise_db")

# Configure connection pool to prevent exhaustion
engine = create_engine(
    DATABASE_URL,
    pool_size=20,          # Increase pool size
    max_overflow=30,       # Allow more overflow connections
    pool_timeout=60,       # Increase timeout to 60 seconds
    pool_recycle=3600,     # Recycle connections every hour
    pool_pre_ping=True,    # Validate connections before use
    echo=False             # Set to True for SQL debugging
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db_session = scoped_session(SessionLocal)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
