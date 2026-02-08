#!/usr/bin/env python3
"""
Development script for NovaFitness API
Provides common development tasks
"""

import sys
import subprocess
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def setup_environment():
    """Setup development environment"""
    print("🔧 Setting up development environment...")
    
    # Create .env from example if it doesn't exist
    env_file = project_root / ".env"
    env_example = project_root / ".env.example"
    
    if not env_file.exists() and env_example.exists():
        import shutil
        shutil.copy(env_example, env_file)
        print(f"✅ Created {env_file} from example")
    
    # Install dependencies
    print("📦 Installing dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    print("✅ Environment setup complete!")


def init_database():
    """Initialize database"""
    print("🗄️  Initializing database...")
    try:
        from app.db.init_db import init_database
        init_database()
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        sys.exit(1)


def run_server():
    """Run development server"""
    print("🚀 Starting development server...")
    try:
        import uvicorn
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except ImportError:
        print("❌ uvicorn not installed. Please run: pip install -r requirements.txt")
        sys.exit(1)


def run_tests():
    """Run test suite"""
    print("🧪 Running tests...")
    subprocess.run([sys.executable, "-m", "pytest", "app/tests/", "-v"])


def show_help():
    """Show help information"""
    print("""
NovaFitness API Development Script

Commands:
  setup     - Setup development environment and install dependencies
  init-db   - Initialize database tables
  server    - Run development server
  test      - Run test suite
  help      - Show this help message

Examples:
  python dev.py setup
  python dev.py init-db
  python dev.py server
  python dev.py test

For first-time setup, run:
  python dev.py setup
  python dev.py init-db
  python dev.py server
    """)


def main():
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == "setup":
        setup_environment()
    elif command == "init-db":
        init_database()
    elif command == "server":
        run_server()
    elif command == "test":
        run_tests()
    elif command == "help":
        show_help()
    else:
        print(f"❌ Unknown command: {command}")
        show_help()
        sys.exit(1)


if __name__ == "__main__":
    main()