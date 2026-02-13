"""
Migration 003: Add daily nutrition tracking table

This migration creates the daily_nutrition table for macronutrient tracking.
"""
from datetime import datetime, timezone
from sqlalchemy import text


def upgrade(connection):
    """Create daily_nutrition table"""
    
    print(f"[{datetime.now(timezone.utc)}] Migration 003: Creating daily_nutrition table...")
    
    # Create daily_nutrition table
    connection.execute(text("""
        CREATE TABLE daily_nutrition (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date DATETIME NOT NULL,
            carbs_consumed REAL NOT NULL DEFAULT 0.0,
            protein_consumed REAL NOT NULL DEFAULT 0.0,
            fat_consumed REAL NOT NULL DEFAULT 0.0,
            carbs_target REAL NOT NULL,
            protein_target REAL NOT NULL,
            fat_target REAL NOT NULL,
            total_calories REAL NOT NULL DEFAULT 0.0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """))
    
    # Create indexes for performance
    connection.execute(text("""
        CREATE INDEX idx_daily_nutrition_user_id ON daily_nutrition (user_id)
    """))
    
    connection.execute(text("""
        CREATE INDEX idx_daily_nutrition_date ON daily_nutrition (date)
    """))
    
    connection.execute(text("""
        CREATE UNIQUE INDEX idx_daily_nutrition_user_date ON daily_nutrition (user_id, date)
    """))
    
    print(f"[{datetime.now(timezone.utc)}] Migration 003: daily_nutrition table created successfully!")


def downgrade(connection):
    """Drop daily_nutrition table"""
    
    print(f"[{datetime.now(timezone.utc)}] Migration 003: Dropping daily_nutrition table...")
    
    # Drop indexes
    connection.execute(text("DROP INDEX IF EXISTS idx_daily_nutrition_user_date"))
    connection.execute(text("DROP INDEX IF EXISTS idx_daily_nutrition_date"))
    connection.execute(text("DROP INDEX IF EXISTS idx_daily_nutrition_user_id"))
    
    # Drop table
    connection.execute(text("DROP TABLE IF EXISTS daily_nutrition"))
    
    print(f"[{datetime.now(timezone.utc)}] Migration 003: daily_nutrition table dropped successfully!")


# Migration metadata
__migration_id__ = "003_add_daily_nutrition_tracking"
__migration_description__ = "Add daily_nutrition table for macronutrient tracking"