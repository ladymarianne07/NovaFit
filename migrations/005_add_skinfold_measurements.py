"""
Migration 005: Add skinfold_measurements table

Stores skinfold inputs and calculated body composition metrics.
"""
from datetime import datetime, timezone
from sqlalchemy import text


def upgrade(connection):
    """Create skinfold_measurements table if it does not exist."""
    print(f"[{datetime.now(timezone.utc)}] Migration 005: Creating skinfold_measurements table...")

    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS skinfold_measurements (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            method VARCHAR(100) NOT NULL,
            measurement_unit VARCHAR(10) NOT NULL DEFAULT 'mm',
            measured_at DATETIME NOT NULL,
            sex VARCHAR(10) NOT NULL,
            age_years INTEGER NOT NULL,
            weight_kg REAL,
            chest_mm REAL,
            midaxillary_mm REAL,
            triceps_mm REAL,
            subscapular_mm REAL,
            abdomen_mm REAL,
            suprailiac_mm REAL,
            thigh_mm REAL,
            sum_of_skinfolds_mm REAL NOT NULL,
            body_density REAL NOT NULL,
            body_fat_percent REAL NOT NULL,
            fat_free_mass_percent REAL NOT NULL,
            fat_mass_kg REAL,
            lean_mass_kg REAL,
            warnings JSON NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """))

    connection.execute(text("""
        CREATE INDEX IF NOT EXISTS ix_skinfold_measurements_user_id
        ON skinfold_measurements (user_id)
    """))

    print(f"[{datetime.now(timezone.utc)}] Migration 005: skinfold_measurements ready")


def downgrade(connection):
    """Drop skinfold_measurements table."""
    print(f"[{datetime.now(timezone.utc)}] Migration 005: Dropping skinfold_measurements table...")
    connection.execute(text("DROP TABLE IF EXISTS skinfold_measurements"))
    print(f"[{datetime.now(timezone.utc)}] Migration 005: rollback completed")


__migration_description__ = "Add skinfold_measurements table for body composition calculations"
