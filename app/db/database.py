from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .models import Base
from ..config import settings


# Create database engine
# SQLite for MVP (single file, no setup required)
engine = create_engine(
    settings.DATABASE_URL,
    # SQLite specific settings
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    # For PostgreSQL migration, remove connect_args and add:
    # pool_pre_ping=True,  # Verify connections before use
    # pool_size=5,         # Connection pool size
    # max_overflow=10      # Max overflow connections
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_database_session() -> Session:
    """
    Dependency to get database session.
    Used by FastAPI dependency injection.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """Drop all database tables (use with caution!)"""
    Base.metadata.drop_all(bind=engine)