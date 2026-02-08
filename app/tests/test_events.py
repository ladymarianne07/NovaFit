def get_auth_header(client, test_user_data):
    """Helper to get authentication header"""
    # Register and login
    client.post("/auth/register", json=test_user_data)
    login_response = client.post("/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_event(client, test_user_data):
    """Test event creation"""
    headers = get_auth_header(client, test_user_data)
    
    event_data = {
        "event_type": "workout",
        "title": "Morning Run",
        "description": "5km run in the park",
        "data": {"distance": 5.0, "duration": 30, "calories": 300}
    }
    
    response = client.post("/events/", json=event_data, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["event_type"] == "workout"
    assert data["title"] == "Morning Run"
    assert data["data"]["distance"] == 5.0


def test_get_user_events(client, test_user_data):
    """Test getting user events"""
    headers = get_auth_header(client, test_user_data)
    
    # Create a test event
    event_data = {
        "event_type": "meal",
        "title": "Breakfast",
        "data": {"calories": 400, "protein": 20}
    }
    client.post("/events/", json=event_data, headers=headers)
    
    # Get events
    response = client.get("/events/", headers=headers)
    assert response.status_code == 200
    events = response.json()
    assert len(events) == 1
    assert events[0]["event_type"] == "meal"


def test_get_event_stats(client, test_user_data):
    """Test getting event statistics"""
    headers = get_auth_header(client, test_user_data)
    
    # Create multiple events
    events = [
        {"event_type": "workout", "title": "Run 1"},
        {"event_type": "workout", "title": "Run 2"},
        {"event_type": "meal", "title": "Lunch"}
    ]
    
    for event in events:
        client.post("/events/", json=event, headers=headers)
    
    # Get stats
    response = client.get("/events/stats/summary", headers=headers)
    assert response.status_code == 200
    stats = response.json()
    assert stats["total_events"] == 3
    assert stats["event_types"]["workout"] == 2
    assert stats["event_types"]["meal"] == 1


def test_unauthorized_access(client):
    """Test that endpoints require authentication"""
    response = client.get("/events/")
    assert response.status_code == 401