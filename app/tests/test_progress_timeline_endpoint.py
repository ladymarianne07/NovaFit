"""
Tests for progress timeline endpoint (GET /users/me/progress/timeline)
Validates historical data aggregation for visualization charts
"""
import pytest


def _register_and_login(client, user_data):
    register_response = client.post("/auth/register", json=user_data)
    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={"email": user_data["email"], "password": user_data["password"]},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_timeline_endpoint_requires_authentication(client):
    """Unauthenticated requests should be rejected"""
    response = client.get("/users/me/progress/timeline")
    assert response.status_code == 401


def test_timeline_returns_valid_structure(client, test_user_data):
    """Timeline response should have expected structure"""
    user_data = {**test_user_data, "email": "timeline-test@example.com", "objective": "fat_loss", "aggressiveness_level": 2}
    headers = _register_and_login(client, user_data)

    # Create some skinfold history to have timeline data
    client.post("/users/me/skinfolds", headers=headers, json={
        "sex": "male",
        "age_years": 25,
        "weight_kg": 80.0,
        "measurement_unit": "mm",
        "chest_mm": 14,
        "midaxillary_mm": 12,
        "triceps_mm": 14,
        "subscapular_mm": 15,
        "abdomen_mm": 24,
        "suprailiac_mm": 18,
        "thigh_mm": 20,
    })

    response = client.get("/users/me/progress/timeline?periodo=semana", headers=headers)
    assert response.status_code == 200

    data = response.json()
    
    # Validate top-level structure
    assert "periodo" in data
    assert "rango_inicio" in data
    assert "rango_fin" in data
    assert "series" in data
    assert "resumen" in data
    assert "advertencias" in data

    assert data["periodo"] == "semana"

    # Validate series structure
    series = data["series"]
    assert "peso" in series
    assert "porcentaje_grasa" in series
    assert "porcentaje_masa_magra" in series
    assert "calorias_diarias" in series
    assert "macros_porcentaje" in series

    # Each timeline should be a list
    assert isinstance(series["peso"], list)
    assert isinstance(series["porcentaje_grasa"], list)
    assert isinstance(series["calorias_diarias"], list)


def test_timeline_supports_different_periods(client, test_user_data):
    """Timeline should accept semana, mes, and anio periods"""
    user_data = {**test_user_data, "email": "timeline-periods@example.com", "objective": "fat_loss", "aggressiveness_level": 2}
    headers = _register_and_login(client, user_data)

    for periodo in ["semana", "mes", "anio"]:
        response = client.get(f"/users/me/progress/timeline?periodo={periodo}", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["periodo"] == periodo


def test_timeline_defaults_to_month(client, test_user_data):
    """Timeline should default to mes when periodo not specified"""
    user_data = {**test_user_data, "email": "timeline-default@example.com", "objective": "fat_loss", "aggressiveness_level": 2}
    headers = _register_and_login(client, user_data)

    response = client.get("/users/me/progress/timeline", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["periodo"] == "mes"
