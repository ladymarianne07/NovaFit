"""Tests for user endpoints in app/api/users.py."""


def test_get_all_users_route_removed(client):
    """GET /users/all was removed in Trello card #3 (no admin role exists,
    no frontend usage, was leaking the full user list anonymously).

    Route should respond 404 regardless of auth state. This test exists so
    that a future re-introduction of the route is forced to also bring back
    proper auth + role checks."""
    response = client.get("/users/all")
    assert response.status_code == 404


def test_get_all_users_route_removed_with_token(client, test_user_data):
    """Same as above but with a valid Bearer token — must also 404."""
    client.post("/auth/register", json=test_user_data)
    login = client.post(
        "/auth/login",
        json={
            "email": test_user_data["email"],
            "password": test_user_data["password"],
        },
    )
    token = login.json()["access_token"]
    response = client.get(
        "/users/all", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404
