#!/usr/bin/env python3
"""Database initialization script"""

import sys
from pathlib import Path

# Add parent directory to path so we can import app modules
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.db.database import create_tables, engine
from app.db.models import Base


def init_database():
    """Initialize the database with tables"""
    print("Creating database tables...")
    try:
        create_tables()
        print("✅ Database tables created successfully!")
        print(f"📍 Database location: {engine.url}")
        
        # Verify tables were created
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"📊 Created tables: {', '.join(tables)}")
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    init_database()