def _register_and_authenticate(client, user_data: dict) -> dict:
    register_response = client.post("/auth/register", json=user_data)
    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={"email": user_data["email"], "password": user_data["password"]},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_intensity_and_objective_change_updates_target_calories(client, test_user_data):
    user_data = {
        **test_user_data,
        "email": "objective-trigger@example.com",
        "objective": "fat_loss",
        "aggressiveness_level": 1,
    }
    headers = _register_and_authenticate(client, user_data)

    me_before = client.get("/users/me", headers=headers)
    assert me_before.status_code == 200
    before = me_before.json()

    update_response = client.put(
        "/users/me/objective",
        headers=headers,
        json={"objective": "fat_loss", "aggressiveness_level": 3},
    )
    assert update_response.status_code == 200
    updated = update_response.json()

    # TDEE is maintenance expenditure and should not change when only intensity/objective changes.
    assert updated["daily_caloric_expenditure"] == before["daily_caloric_expenditure"]
    # Objective target must change with aggressiveness.
    assert updated["target_calories"] != before["target_calories"]


def test_age_change_triggers_tdee_and_target_recalculation(client, test_user_data):
    user_data = {
        **test_user_data,
        "email": "age-trigger@example.com",
        "objective": "muscle_gain",
        "aggressiveness_level": 2,
    }
    headers = _register_and_authenticate(client, user_data)

    before = client.get("/users/me", headers=headers).json()

    update_response = client.put(
        "/users/me/biometrics",
        headers=headers,
        json={"age": before["age"] + 5},
    )
    assert update_response.status_code == 200
    updated = update_response.json()

    assert updated["daily_caloric_expenditure"] != before["daily_caloric_expenditure"]
    assert updated["target_calories"] != before["target_calories"]


def test_height_and_gender_change_trigger_tdee_and_target_recalculation(client, test_user_data):
    user_data = {
        **test_user_data,
        "email": "height-gender-trigger@example.com",
        "objective": "fat_loss",
        "aggressiveness_level": 2,
    }
    headers = _register_and_authenticate(client, user_data)

    before = client.get("/users/me", headers=headers).json()

    # Height trigger
    height_response = client.put(
        "/users/me/biometrics",
        headers=headers,
        json={"height": before["height"] + 5},
    )
    assert height_response.status_code == 200
    after_height = height_response.json()

    assert after_height["daily_caloric_expenditure"] != before["daily_caloric_expenditure"]
    assert after_height["target_calories"] != before["target_calories"]

    # Gender trigger
    new_gender = "female" if after_height["gender"] == "male" else "male"
    gender_response = client.put(
        "/users/me/biometrics",
        headers=headers,
        json={"gender": new_gender},
    )
    assert gender_response.status_code == 200
    after_gender = gender_response.json()

    assert after_gender["daily_caloric_expenditure"] != after_height["daily_caloric_expenditure"]
    assert after_gender["target_calories"] != after_height["target_calories"]
