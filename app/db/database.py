import logging
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, Session
from .models import Base
from .workout_seed import seed_exercise_activities
from ..models.food import FoodEntry  # noqa: F401 - ensure model registration
from ..models.food_portion_cache import FoodPortionCache  # noqa: F401 - ensure model registration
from ..config import settings


logger = logging.getLogger(__name__)


REQUIRED_USER_COLUMNS: dict[str, str] = {
    "objective": "VARCHAR(50)",
    "aggressiveness_level": "INTEGER",
    "target_calories": "REAL",
    "protein_target_g": "REAL",
    "fat_target_g": "REAL",
    "carbs_target_g": "REAL",
    "custom_target_calories": "REAL",
    "carbs_target_percent": "REAL",
    "protein_target_percent": "REAL",
    "fat_target_percent": "REAL",
    "role": "VARCHAR(20) DEFAULT 'student'",
}

REQUIRED_ROUTINE_COLUMNS: dict[str, str] = {
    "source_type": "VARCHAR(20) DEFAULT 'file'",
    "health_analysis": "TEXT",
    "intake_data": "TEXT",
}


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
    """Create all database tables and ensure backward-compatible schema updates."""
    Base.metadata.create_all(bind=engine)
    ensure_schema_compatibility()

    with engine.begin() as connection:
        seed_stats = seed_exercise_activities(connection)
        logger.info(
            "Workout activities seed applied (inserted=%s, updated=%s)",
            seed_stats["inserted"],
            seed_stats["updated"],
        )


def ensure_schema_compatibility() -> None:
    """
    Ensure local SQLite schema remains compatible with current models.

    This avoids runtime failures on existing databases created before
    new columns were introduced (for example, users.objective).
    """
    if "sqlite" not in settings.DATABASE_URL:
        return

    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    if "food_portion_cache" not in table_names:
        logger.info("Creating missing table: food_portion_cache")
        Base.metadata.create_all(bind=engine)

    missing_user_cols = get_missing_user_columns()
    if missing_user_cols:
        logger.info("Detected missing users columns: %s", ", ".join(missing_user_cols))
        with engine.begin() as connection:
            for column_name in missing_user_cols:
                column_type = REQUIRED_USER_COLUMNS[column_name]
                connection.execute(text(f"ALTER TABLE users ADD COLUMN {column_name} {column_type} DEFAULT NULL"))
                logger.info("Added missing column users.%s", column_name)

    missing_routine_cols = get_missing_routine_columns()
    if missing_routine_cols:
        logger.info("Detected missing user_routines columns: %s", ", ".join(missing_routine_cols))
        with engine.begin() as connection:
            for column_name in missing_routine_cols:
                column_type = REQUIRED_ROUTINE_COLUMNS[column_name]
                connection.execute(text(f"ALTER TABLE user_routines ADD COLUMN {column_name} {column_type} DEFAULT NULL"))
                logger.info("Added missing column user_routines.%s", column_name)


def get_missing_user_columns() -> list[str]:
    """Return missing required columns in users table for SQLite databases."""
    if "sqlite" not in settings.DATABASE_URL:
        return []

    inspector = inspect(engine)
    table_names = inspector.get_table_names()

    if "users" not in table_names:
        return list(REQUIRED_USER_COLUMNS.keys())

    existing_columns = {column["name"] for column in inspector.get_columns("users")}

    return [
        column_name
        for column_name in REQUIRED_USER_COLUMNS.keys()
        if column_name not in existing_columns
    ]


def get_missing_routine_columns() -> list[str]:
    """Return missing required columns in user_routines table for SQLite databases."""
    if "sqlite" not in settings.DATABASE_URL:
        return []

    inspector = inspect(engine)
    table_names = inspector.get_table_names()

    if "user_routines" not in table_names:
        return []  # Table doesn't exist yet; create_all handles it

    existing_columns = {column["name"] for column in inspector.get_columns("user_routines")}

    return [
        column_name
        for column_name in REQUIRED_ROUTINE_COLUMNS.keys()
        if column_name not in existing_columns
    ]


def drop_tables():
    """Drop all database tables (use with caution!)"""
    Base.metadata.drop_all(bind=engine)