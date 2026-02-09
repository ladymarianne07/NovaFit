"""
Migration: Update user schema for complete required registration
- Make first_name and last_name required (NOT NULL)
- Rename daily_caloric_expenditure to tdee for consistency
"""
import logging
from sqlalchemy import text, MetaData, Table
from ..app.db.database import get_database_engine

logger = logging.getLogger(__name__)


def upgrade():
    """
    Upgrade database schema for complete required registration
    """
    engine = get_database_engine()
    
    logger.info("Starting user schema update migration...")
    
    with engine.connect() as connection:
        trans = connection.begin()
        
        try:
            # Check for users with empty first_name or last_name
            result = connection.execute(text("""
                SELECT id, email, first_name, last_name FROM users 
                WHERE first_name IS NULL 
                   OR first_name = '' 
                   OR last_name IS NULL 
                   OR last_name = ''
            """))
            
            incomplete_users = result.fetchall()
            
            if incomplete_users:
                logger.warning(f"Found {len(incomplete_users)} users with incomplete name data. Updating...")
                
                # Update users with missing names
                for user in incomplete_users:
                    first_name = user.first_name or f"User{user.id}"
                    last_name = user.last_name or "Unknown"
                    
                    connection.execute(text("""
                        UPDATE users 
                        SET first_name = :first_name, last_name = :last_name 
                        WHERE id = :user_id
                    """), {
                        'first_name': first_name,
                        'last_name': last_name,
                        'user_id': user.id
                    })
                    
                    logger.info(f"Updated user {user.id} ({user.email}): {first_name} {last_name}")
            
            # PostgreSQL: Rename column and add NOT NULL constraints
            if engine.dialect.name == 'postgresql':
                logger.info("Applying PostgreSQL migrations...")
                
                # Rename daily_caloric_expenditure to tdee
                connection.execute(text("""
                    ALTER TABLE users 
                    RENAME COLUMN daily_caloric_expenditure TO tdee
                """))
                
                # Make first_name and last_name NOT NULL
                connection.execute(text("""
                    ALTER TABLE users 
                    ALTER COLUMN first_name SET NOT NULL
                """))
                
                connection.execute(text("""
                    ALTER TABLE users 
                    ALTER COLUMN last_name SET NOT NULL
                """))
            
            # SQLite: Create new table and migrate data
            elif engine.dialect.name == 'sqlite':
                logger.info("Applying SQLite migrations...")
                
                # Create new users table with updated schema
                connection.execute(text("""
                    CREATE TABLE users_new (
                        id INTEGER PRIMARY KEY,
                        email VARCHAR(255) NOT NULL UNIQUE,
                        hashed_password VARCHAR(255) NOT NULL,
                        first_name VARCHAR(100) NOT NULL,
                        last_name VARCHAR(100) NOT NULL,
                        is_active BOOLEAN DEFAULT 1,
                        age INTEGER NOT NULL,
                        gender VARCHAR(10) NOT NULL,
                        weight FLOAT NOT NULL,
                        height FLOAT NOT NULL,
                        activity_level FLOAT NOT NULL,
                        bmr FLOAT NOT NULL,
                        tdee FLOAT NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME,
                        last_login DATETIME
                    )
                """))
                
                # Copy data from old table to new table
                connection.execute(text("""
                    INSERT INTO users_new (
                        id, email, hashed_password, first_name, last_name, is_active,
                        age, gender, weight, height, activity_level, bmr, tdee,
                        created_at, updated_at, last_login
                    )
                    SELECT 
                        id, email, hashed_password, first_name, last_name, is_active,
                        age, gender, weight, height, activity_level, bmr, daily_caloric_expenditure,
                        created_at, updated_at, last_login
                    FROM users
                """))
                
                # Drop old table and rename new table
                connection.execute(text("DROP TABLE users"))
                connection.execute(text("ALTER TABLE users_new RENAME TO users"))
                
                # Recreate indexes
                connection.execute(text("CREATE UNIQUE INDEX idx_users_email ON users (email)"))
                connection.execute(text("CREATE INDEX idx_users_id ON users (id)"))
            
            # Commit transaction
            trans.commit()
            logger.info("✅ User schema migration completed successfully!")
            
        except Exception as e:
            trans.rollback()
            logger.error(f"❌ Migration failed: {e}")
            raise


def downgrade():
    """
    Downgrade database schema (reverse the migration)
    """
    engine = get_database_engine()
    
    logger.info("Starting user schema downgrade migration...")
    
    with engine.connect() as connection:
        trans = connection.begin()
        
        try:
            if engine.dialect.name == 'postgresql':
                # Reverse PostgreSQL changes
                connection.execute(text("""
                    ALTER TABLE users 
                    RENAME COLUMN tdee TO daily_caloric_expenditure
                """))
                
                connection.execute(text("""
                    ALTER TABLE users 
                    ALTER COLUMN first_name DROP NOT NULL
                """))
                
                connection.execute(text("""
                    ALTER TABLE users 
                    ALTER COLUMN last_name DROP NOT NULL
                """))
            
            elif engine.dialect.name == 'sqlite':
                # For SQLite, we'd need to recreate the table again
                # This is a simplified version - in production, you'd want more careful handling
                logger.warning("SQLite downgrade not fully implemented - manual intervention may be required")
            
            trans.commit()
            logger.info("✅ User schema downgrade completed!")
            
        except Exception as e:
            trans.rollback()
            logger.error(f"❌ Downgrade failed: {e}")
            raise


if __name__ == "__main__":
    # Running migration directly
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        downgrade()
    else:
        upgrade()