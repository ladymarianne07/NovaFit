"""
Migration 006: Add workout module tables and initial MET catalog.

Creates:
- exercise_activities
- workout_sessions
- workout_session_blocks
- workout_correction_factors
- exercise_daily_energy_log
"""
from datetime import datetime, timezone
from sqlalchemy import text
from sqlalchemy.engine import Connection


def upgrade(connection: Connection):
    """Create workout-related tables and indexes, then seed activities."""
    print(f"[{datetime.now(timezone.utc)}] Migration 006: Creating workout tables...")

    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS exercise_activities (
            id INTEGER PRIMARY KEY,
            activity_key VARCHAR(100) NOT NULL UNIQUE,
            category VARCHAR(100) NOT NULL,
            label_es VARCHAR(150) NOT NULL,
            met_low REAL NOT NULL,
            met_medium REAL NOT NULL,
            met_high REAL NOT NULL,
            source_refs JSON NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME
        )
    """))

    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS workout_sessions (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            session_date DATE NOT NULL,
            started_at DATETIME,
            ended_at DATETIME,
            source VARCHAR(20) NOT NULL DEFAULT 'ai',
            status VARCHAR(20) NOT NULL DEFAULT 'draft',
            raw_input TEXT,
            ai_output JSON,
            total_kcal_min REAL,
            total_kcal_max REAL,
            total_kcal_est REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """))

    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS workout_session_blocks (
            id INTEGER PRIMARY KEY,
            session_id INTEGER NOT NULL,
            activity_id INTEGER NOT NULL,
            block_order INTEGER NOT NULL,
            duration_minutes INTEGER NOT NULL,
            intensity_level VARCHAR(20),
            intensity_raw VARCHAR(120),
            weight_kg_used REAL,
            met_used_min REAL,
            met_used_max REAL,
            correction_factor REAL NOT NULL DEFAULT 1.0,
            kcal_min REAL,
            kcal_max REAL,
            kcal_est REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(session_id) REFERENCES workout_sessions(id),
            FOREIGN KEY(activity_id) REFERENCES exercise_activities(id)
        )
    """))

    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS workout_correction_factors (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            scope VARCHAR(20) NOT NULL DEFAULT 'global',
            category VARCHAR(100),
            activity_key VARCHAR(100),
            factor REAL NOT NULL DEFAULT 1.0,
            method VARCHAR(30) NOT NULL DEFAULT 'manual',
            effective_from DATE NOT NULL,
            effective_to DATE,
            updated_at DATETIME,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """))

    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS exercise_daily_energy_log (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            log_date DATE NOT NULL,
            exercise_kcal_min REAL NOT NULL DEFAULT 0.0,
            exercise_kcal_max REAL NOT NULL DEFAULT 0.0,
            exercise_kcal_est REAL NOT NULL DEFAULT 0.0,
            intake_kcal REAL NOT NULL DEFAULT 0.0,
            net_kcal_est REAL NOT NULL DEFAULT 0.0,
            updated_at DATETIME,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """))

    # Indexes
    connection.execute(text("""
        CREATE INDEX IF NOT EXISTS ix_exercise_activities_activity_key
        ON exercise_activities (activity_key)
    """))
    connection.execute(text("""
        CREATE INDEX IF NOT EXISTS ix_exercise_activities_category
        ON exercise_activities (category)
    """))

    connection.execute(text("""
        CREATE INDEX IF NOT EXISTS ix_workout_sessions_user_id
        ON workout_sessions (user_id)
    """))
    connection.execute(text("""
        CREATE INDEX IF NOT EXISTS ix_workout_sessions_session_date
        ON workout_sessions (session_date)
    """))

    connection.execute(text("""
        CREATE INDEX IF NOT EXISTS ix_workout_session_blocks_session_id
        ON workout_session_blocks (session_id)
    """))
    connection.execute(text("""
        CREATE INDEX IF NOT EXISTS ix_workout_session_blocks_activity_id
        ON workout_session_blocks (activity_id)
    """))

    connection.execute(text("""
        CREATE INDEX IF NOT EXISTS ix_workout_correction_factors_user_id
        ON workout_correction_factors (user_id)
    """))

    connection.execute(text("""
        CREATE INDEX IF NOT EXISTS ix_exercise_daily_energy_log_user_id
        ON exercise_daily_energy_log (user_id)
    """))
    connection.execute(text("""
        CREATE INDEX IF NOT EXISTS ix_exercise_daily_energy_log_log_date
        ON exercise_daily_energy_log (log_date)
    """))
    connection.execute(text("""
        CREATE UNIQUE INDEX IF NOT EXISTS ix_exercise_daily_energy_log_user_date
        ON exercise_daily_energy_log (user_id, log_date)
    """))

    # Seed initial MET catalog
    try:
        from app.db.workout_seed import seed_exercise_activities

        seed_stats = seed_exercise_activities(connection)
        print(
            f"[{datetime.now(timezone.utc)}] Migration 006: exercise_activities seeded "
            f"(inserted={seed_stats['inserted']}, updated={seed_stats['updated']})"
        )
    except Exception as exc:
        print(f"[{datetime.now(timezone.utc)}] Migration 006: seed skipped due to error: {exc}")

    print(f"[{datetime.now(timezone.utc)}] Migration 006: workout tables ready")


def downgrade(connection: Connection):
    """Drop workout module tables in reverse dependency order."""
    print(f"[{datetime.now(timezone.utc)}] Migration 006: Dropping workout tables...")

    connection.execute(text("DROP TABLE IF EXISTS workout_session_blocks"))
    connection.execute(text("DROP TABLE IF EXISTS workout_sessions"))
    connection.execute(text("DROP TABLE IF EXISTS workout_correction_factors"))
    connection.execute(text("DROP TABLE IF EXISTS exercise_daily_energy_log"))
    connection.execute(text("DROP TABLE IF EXISTS exercise_activities"))

    print(f"[{datetime.now(timezone.utc)}] Migration 006: rollback completed")


__migration_description__ = "Add workout module tables and initial MET catalog"
