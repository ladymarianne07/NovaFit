import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.database import get_database_session
from app.db.models import Base
from app.db.workout_seed import seed_exercise_activities


# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_database_session] = override_get_db


@pytest.fixture
def client():
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        seed_exercise_activities(conn)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user_data():
    return {
        "email": "test@example.com",
        "password": "testpassword123",
        "first_name": "Test",
        "last_name": "User",
        "gender": "male",
        "weight": 70.0,
        "height": 175.0,
        "age": 25,
        "activity_level": 1.5
    }


@pytest.fixture
def authed_client(client, test_user_data):
    """TestClient with a registered+logged-in user. The Bearer token is set
    as a default header so endpoint calls behave as authenticated requests."""
    client.post("/auth/register", json=test_user_data)
    login = client.post(
        "/auth/login",
        json={
            "email": test_user_data["email"],
            "password": test_user_data["password"],
        },
    )
    token = login.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client