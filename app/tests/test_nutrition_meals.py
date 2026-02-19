def _get_auth_header(client, test_user_data):
    client.post("/auth/register", json=test_user_data)
    login_response = client.post(
        "/auth/login",
        json={"email": test_user_data["email"], "password": test_user_data["password"]},
    )
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_get_and_delete_meals(client, test_user_data):
    headers = _get_auth_header(client, test_user_data)

    meal_group_id = "test-meal-group"
    meal_payload = {
        "meal_type": "meal",
        "meal_group_id": meal_group_id,
        "meal_label": "Comida 1",
        "food_name": "coffee",
        "quantity_grams": 100,
        "calories_per_100g": 1,
        "carbs_per_100g": 0,
        "protein_per_100g": 0,
        "fat_per_100g": 0,
    }

    log_response = client.post("/nutrition/meals", json=meal_payload, headers=headers)
    assert log_response.status_code == 200

    second_payload = {
        "meal_type": "meal",
        "meal_group_id": meal_group_id,
        "meal_label": "Comida 1",
        "food_name": "eggs",
        "quantity_grams": 50,
        "calories_per_100g": 155,
        "carbs_per_100g": 1.1,
        "protein_per_100g": 13,
        "fat_per_100g": 11,
    }

    second_response = client.post("/nutrition/meals", json=second_payload, headers=headers)
    assert second_response.status_code == 200

    list_response = client.get("/nutrition/meals", headers=headers)
    assert list_response.status_code == 200
    meals = list_response.json()
    matching = [meal for meal in meals if meal["id"] == meal_group_id]
    assert len(matching) == 1
    assert len(matching[0]["items"]) == 2

    delete_response = client.delete(f"/nutrition/meals/{meal_group_id}", headers=headers)
    assert delete_response.status_code == 200

    list_after = client.get("/nutrition/meals", headers=headers)
    assert list_after.status_code == 200
    meals_after = list_after.json()
    assert all(meal["id"] != meal_group_id for meal in meals_after)
