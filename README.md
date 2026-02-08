# NovaFitness Backend

Private pilot web app backend built with FastAPI, designed for local development with future cloud migration support.

## Architecture Overview

- **Backend**: FastAPI (Python)
- **Database**: SQLite (MVP) → PostgreSQL (Production)
- **ORM**: SQLAlchemy 2.0
- **Auth**: JWT tokens with email/password
- **API**: RESTful, JSON-only

## Quick Start

```bash
# Setup environment
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Setup database
python -m app.db.init_db

# Run development server
python -m app.main
```

## Project Structure

```
app/
├── main.py              # FastAPI application entry point
├── config.py            # Configuration management
├── dependencies.py      # Dependency injection
├── api/                 # API routes
│   ├── __init__.py
│   ├── auth.py          # Authentication endpoints
│   ├── users.py         # User management
│   └── events.py        # Event/activity tracking
├── core/                # Core business logic
│   ├── __init__.py
│   ├── auth.py          # Authentication logic
│   ├── security.py      # Password hashing, JWT
│   └── exceptions.py    # Custom exceptions
├── db/                  # Database layer
│   ├── __init__.py
│   ├── init_db.py       # Database initialization
│   ├── models.py        # SQLAlchemy models
│   └── database.py      # Database connection
├── schemas/             # Pydantic models
│   ├── __init__.py
│   ├── user.py          # User schemas
│   └── event.py         # Event schemas
└── tests/               # Test suite
    ├── __init__.py
    ├── conftest.py
    ├── test_auth.py
    └── test_events.py
```

## MVP vs Future-Ready

### MVP Features ✓
- SQLite database
- Basic JWT auth
- User registration/login
- Event CRUD operations
- Data isolation per user

### Future Enhancements 🔄
- PostgreSQL migration
- Refresh token rotation
- Rate limiting
- Event aggregations/analytics
- Real-time notifications
- Cloud deployment scripts

## Security Considerations

- Passwords hashed with bcrypt
- JWT tokens with 1-year expiration (persistent sessions)
- CORS configured for PWA
- SQL injection protection via ORM
- User data isolation enforced at DB level

**Session Management**: Users remain logged in until they manually log out or their browser data is cleared. This provides a seamless PWA experience without frequent re-authentication.

## Database Migration Path

The codebase is designed to switch from SQLite to PostgreSQL by simply changing the `DATABASE_URL` in configuration. All SQL operations use SQLAlchemy ORM for database independence.