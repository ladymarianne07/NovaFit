"""Tests for user endpoints in app/api/users.py."""


def _register_and_token(client, test_user_data) -> str:
    """Helper: register the test user and return a Bearer token."""
    client.post("/auth/register", json=test_user_data)
    login = client.post(
        "/auth/login",
        json={
            "email": test_user_data["email"],
            "password": test_user_data["password"],
        },
    )
    return login.json()["access_token"]


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


# ── Trello card #5: update_user_objective error handling ─────────────────────


def test_update_user_objective_valid_returns_200(client, test_user_data):
    """Happy path: valid objective + aggressiveness updates user and returns 200."""
    token = _register_and_token(client, test_user_data)
    response = client.put(
        "/users/me/objective",
        headers={"Authorization": f"Bearer {token}"},
        json={"objective": "fat_loss", "aggressiveness_level": 2},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["objective"] == "fat_loss"
    assert body["aggressiveness_level"] == 2
    assert body["target_calories"] is not None
    assert body["protein_target_g"] is not None


def test_update_user_objective_invalid_aggressiveness_returns_422(client, test_user_data):
    """Pydantic schema rejects aggressiveness_level outside 1..3 with 422,
    not the previous opaque 400 'Failed to update objective'."""
    token = _register_and_token(client, test_user_data)
    response = client.put(
        "/users/me/objective",
        headers={"Authorization": f"Bearer {token}"},
        json={"objective": "fat_loss", "aggressiveness_level": 99},
    )
    assert response.status_code == 422


def test_update_user_objective_internal_error_propagates(
    client, test_user_data, monkeypatch
):
    """Unexpected internal errors must propagate to the framework's exception
    handling (which converts them to 500 in production), NOT be silenced as a
    400 'Failed to update objective' as the old code did.

    TestClient with default raise_server_exceptions=True surfaces the raw
    exception in the test — we assert that, which proves the endpoint does NOT
    have a broad try/except hiding it. In production the global Exception
    handler in main.py converts the same exception to a 500 JSON response."""
    import pytest
    from app.services.user_service import UserService

    def boom(self, *_args, **_kwargs):
        raise RuntimeError("simulated internal failure")

    monkeypatch.setattr(UserService, "update_user_objective", boom)

    token = _register_and_token(client, test_user_data)
    with pytest.raises(RuntimeError, match="simulated internal failure"):
        client.put(
            "/users/me/objective",
            headers={"Authorization": f"Bearer {token}"},
            json={"objective": "fat_loss", "aggressiveness_level": 2},
        )
