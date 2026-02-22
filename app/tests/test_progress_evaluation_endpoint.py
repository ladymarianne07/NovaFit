def _register_and_login(client, user_data: dict) -> dict:
    register_response = client.post("/auth/register", json=user_data)
    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={"email": user_data["email"], "password": user_data["password"]},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_progress_evaluation_endpoint_returns_valid_shape(client, test_user_data):
    user_data = {
        **test_user_data,
        "email": "progress-endpoint@example.com",
        "objective": "fat_loss",
        "aggressiveness_level": 2,
    }
    headers = _register_and_login(client, user_data)

    # Create two skinfold history entries so endpoint can evaluate trend
    first = client.post(
        "/users/me/skinfolds",
        headers=headers,
        json={
            "sex": "male",
            "age_years": 25,
            "weight_kg": 80,
            "measurement_unit": "mm",
            "chest_mm": 14,
            "midaxillary_mm": 12,
            "triceps_mm": 14,
            "subscapular_mm": 15,
            "abdomen_mm": 24,
            "suprailiac_mm": 18,
            "thigh_mm": 20,
        },
    )
    assert first.status_code == 200

    second = client.post(
        "/users/me/skinfolds",
        headers=headers,
        json={
            "sex": "male",
            "age_years": 25,
            "weight_kg": 78.5,
            "measurement_unit": "mm",
            "chest_mm": 12,
            "midaxillary_mm": 10,
            "triceps_mm": 12,
            "subscapular_mm": 13,
            "abdomen_mm": 20,
            "suprailiac_mm": 16,
            "thigh_mm": 18,
        },
    )
    assert second.status_code == 200

    response = client.post("/users/me/progress-evaluation", headers=headers, json={"periodo": "mes"})
    assert response.status_code == 200

    data = response.json()
    assert set(data.keys()) == {"periodo", "score", "estado", "resumen", "metricas", "advertencias"}
    assert data["periodo"] == "mes"
    assert -100 <= data["score"] <= 100
    assert data["estado"] in {"Progreso positivo", "Estable", "Desviación del objetivo"}
    assert isinstance(data["resumen"], str)
    assert set(data["metricas"].keys()) == {"deltaPeso", "deltaGrasa", "deltaMagra"}
    assert isinstance(data["advertencias"], list)


def test_progress_evaluation_endpoint_handles_insufficient_history(client, test_user_data):
    user_data = {
        **test_user_data,
        "email": "progress-insufficient@example.com",
        "objective": "maintenance",
    }
    headers = _register_and_login(client, user_data)

    response = client.post("/users/me/progress-evaluation", headers=headers, json={"periodo": "semana"})
    assert response.status_code == 200
    data = response.json()

    assert data["periodo"] == "semana"
    assert data["estado"] == "Estable"
    assert any("insuficient" in warning.lower() for warning in data["advertencias"])


def test_progress_evaluation_endpoint_defaults_to_month_when_body_missing(client, test_user_data):
    user_data = {
        **test_user_data,
        "email": "progress-default-period@example.com",
        "objective": "maintenance",
    }
    headers = _register_and_login(client, user_data)

    response = client.post("/users/me/progress-evaluation", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["periodo"] == "mes"
