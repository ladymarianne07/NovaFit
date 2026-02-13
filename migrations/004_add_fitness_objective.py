"""
Migration 004: Add fitness objective and personalized targets

This migration adds objective-based calorie and macro targets to the users table.
"""
from datetime import datetime, timezone
from sqlalchemy import text


def upgrade(connection):
    """Add objective and target columns to users table"""
    
    print(f"[{datetime.now(timezone.utc)}] Migration 004: Adding fitness objective columns...")
    
    # Add objective column
    try:
        connection.execute(text("""
            ALTER TABLE users ADD COLUMN objective VARCHAR(50) DEFAULT NULL
        """))
        print(f"[{datetime.now(timezone.utc)}] Added objective column")
    except Exception as e:
        print(f"[{datetime.now(timezone.utc)}] Column objective already exists or error: {e}")
    
    # Add aggressiveness_level column
    try:
        connection.execute(text("""
            ALTER TABLE users ADD COLUMN aggressiveness_level INTEGER DEFAULT NULL
        """))
        print(f"[{datetime.now(timezone.utc)}] Added aggressiveness_level column")
    except Exception as e:
        print(f"[{datetime.now(timezone.utc)}] Column aggressiveness_level already exists or error: {e}")
    
    # Add target_calories column
    try:
        connection.execute(text("""
            ALTER TABLE users ADD COLUMN target_calories REAL DEFAULT NULL
        """))
        print(f"[{datetime.now(timezone.utc)}] Added target_calories column")
    except Exception as e:
        print(f"[{datetime.now(timezone.utc)}] Column target_calories already exists or error: {e}")
    
    # Add protein_target_g column
    try:
        connection.execute(text("""
            ALTER TABLE users ADD COLUMN protein_target_g REAL DEFAULT NULL
        """))
        print(f"[{datetime.now(timezone.utc)}] Added protein_target_g column")
    except Exception as e:
        print(f"[{datetime.now(timezone.utc)}] Column protein_target_g already exists or error: {e}")
    
    # Add fat_target_g column
    try:
        connection.execute(text("""
            ALTER TABLE users ADD COLUMN fat_target_g REAL DEFAULT NULL
        """))
        print(f"[{datetime.now(timezone.utc)}] Added fat_target_g column")
    except Exception as e:
        print(f"[{datetime.now(timezone.utc)}] Column fat_target_g already exists or error: {e}")
    
    # Add carbs_target_g column
    try:
        connection.execute(text("""
            ALTER TABLE users ADD COLUMN carbs_target_g REAL DEFAULT NULL
        """))
        print(f"[{datetime.now(timezone.utc)}] Added carbs_target_g column")
    except Exception as e:
        print(f"[{datetime.now(timezone.utc)}] Column carbs_target_g already exists or error: {e}")
    
    print(f"[{datetime.now(timezone.utc)}] Migration 004: Fitness objective columns added successfully!")


def downgrade(connection):
    """Remove objective and target columns from users table"""
    
    print(f"[{datetime.now(timezone.utc)}] Migration 004: Rolling back fitness objective columns...")
    
    columns_to_drop = [
        'objective',
        'aggressiveness_level',
        'target_calories',
        'protein_target_g',
        'fat_target_g',
        'carbs_target_g'
    ]
    
    for column in columns_to_drop:
        try:
            connection.execute(text(f"""
                ALTER TABLE users DROP COLUMN {column}
            """))
            print(f"[{datetime.now(timezone.utc)}] Dropped {column} column")
        except Exception as e:
            print(f"[{datetime.now(timezone.utc)}] Could not drop {column} or already removed: {e}")
    
    print(f"[{datetime.now(timezone.utc)}] Migration 004: Rollback completed!")


__migration_description__ = "Add fitness objective and personalized calorie/macro targets"
