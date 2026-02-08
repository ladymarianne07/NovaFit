def test_register_user(client, test_user_data):
    """Test user registration"""
    response = client.post("/auth/register", json=test_user_data)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == test_user_data["email"]
    assert "id" in data
    assert "hashed_password" not in data  # Should not expose password


def test_register_duplicate_user(client, test_user_data):
    """Test duplicate user registration fails"""
    # Register first user
    client.post("/auth/register", json=test_user_data)
    
    # Try to register same user again
    response = client.post("/auth/register", json=test_user_data)
    assert response.status_code == 409


def test_login_user(client, test_user_data):
    """Test user login"""
    # Register user first
    client.post("/auth/register", json=test_user_data)
    
    # Login
    login_data = {
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    }
    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials(client, test_user_data):
    """Test login with invalid credentials"""
    login_data = {
        "email": "nonexistent@example.com",
        "password": "wrongpassword"
    }
    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 401