"""
Migration: Make biometric fields required
"""
import logging
from sqlalchemy import text
from ..app.db.database import get_database_engine

logger = logging.getLogger(__name__)


def upgrade():
    """
    Upgrade database schema to make biometric fields required
    
    IMPORTANT: This migration will fail if there are existing users without complete biometric data.
    Run the provided data migration script first to populate missing data or remove incomplete users.
    """
    engine = get_database_engine()
    
    logger.info("Starting biometric fields migration...")
    
    with engine.connect() as connection:
        # Start transaction
        trans = connection.begin()
        
        try:
            # Check for users with incomplete biometric data
            result = connection.execute(text("""
                SELECT id, email FROM users 
                WHERE age IS NULL 
                   OR gender IS NULL 
                   OR weight IS NULL 
                   OR height IS NULL 
                   OR activity_level IS NULL 
                   OR bmr IS NULL 
                   OR daily_caloric_expenditure IS NULL
            """))
            
            incomplete_users = result.fetchall()
            
            if incomplete_users:
                logger.error(f"Found {len(incomplete_users)} users with incomplete biometric data:")
                for user in incomplete_users:
                    logger.error(f"  - User ID {user.id}: {user.email}")
                
                raise ValueError(
                    f"Cannot make biometric fields required. "
                    f"Found {len(incomplete_users)} users with incomplete data. "
                    f"Please run the data migration script first or remove incomplete users."
                )
            
            # Make fields NOT NULL
            logger.info("Making biometric fields required...")
            
            # Note: SQL Server syntax - adjust for your database if different
            connection.execute(text("ALTER TABLE users ALTER COLUMN age INTEGER NOT NULL"))
            connection.execute(text("ALTER TABLE users ALTER COLUMN gender VARCHAR(10) NOT NULL"))
            connection.execute(text("ALTER TABLE users ALTER COLUMN weight FLOAT NOT NULL"))
            connection.execute(text("ALTER TABLE users ALTER COLUMN height FLOAT NOT NULL"))
            connection.execute(text("ALTER TABLE users ALTER COLUMN activity_level FLOAT NOT NULL"))
            connection.execute(text("ALTER TABLE users ALTER COLUMN bmr FLOAT NOT NULL"))
            connection.execute(text("ALTER TABLE users ALTER COLUMN daily_caloric_expenditure FLOAT NOT NULL"))
            
            # Commit transaction
            trans.commit()
            logger.info("✅ Migration completed successfully!")
            
        except Exception as e:
            # Rollback on error
            trans.rollback()
            logger.error(f"❌ Migration failed: {e}")
            raise


def downgrade():
    """
    Downgrade database schema to make biometric fields optional again
    """
    engine = get_database_engine()
    
    logger.info("Reverting biometric fields migration...")
    
    with engine.connect() as connection:
        # Start transaction
        trans = connection.begin()
        
        try:
            # Make fields nullable again
            logger.info("Making biometric fields optional...")
            
            connection.execute(text("ALTER TABLE users ALTER COLUMN age INTEGER NULL"))
            connection.execute(text("ALTER TABLE users ALTER COLUMN gender VARCHAR(10) NULL"))
            connection.execute(text("ALTER TABLE users ALTER COLUMN weight FLOAT NULL"))
            connection.execute(text("ALTER TABLE users ALTER COLUMN height FLOAT NULL"))
            connection.execute(text("ALTER TABLE users ALTER COLUMN activity_level FLOAT NULL"))
            connection.execute(text("ALTER TABLE users ALTER COLUMN bmr FLOAT NULL"))
            connection.execute(text("ALTER TABLE users ALTER COLUMN daily_caloric_expenditure FLOAT NULL"))
            
            # Commit transaction
            trans.commit()
            logger.info("✅ Downgrade completed successfully!")
            
        except Exception as e:
            # Rollback on error
            trans.rollback()
            logger.error(f"❌ Downgrade failed: {e}")
            raise


if __name__ == "__main__":
    # Run migration
    upgrade()