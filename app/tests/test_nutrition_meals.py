from app.db.models import Event
from app.tests.conftest import TestingSessionLocal


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


def test_delete_meal_rolls_back_totals_when_event_totals_are_missing(client, test_user_data):
    headers = _get_auth_header(client, test_user_data)

    meal_group_id = "legacy-group"
    meal_payload = {
        "meal_type": "meal",
        "meal_group_id": meal_group_id,
        "meal_label": "Comida legacy",
        "food_name": "banana",
        "quantity_grams": 150,
        "calories_per_100g": 89,
        "carbs_per_100g": 22.8,
        "protein_per_100g": 1.1,
        "fat_per_100g": 0.3,
    }

    log_response = client.post("/nutrition/meals", json=meal_payload, headers=headers)
    assert log_response.status_code == 200

    before_delete = client.get("/nutrition/macros", headers=headers)
    assert before_delete.status_code == 200
    before_data = before_delete.json()
    assert before_data["total_calories"] > 0
    assert before_data["carbs"] > 0

    with TestingSessionLocal() as db:
        events = (
            db.query(Event)
            .filter(Event.event_type == "meal", Event.is_deleted == False)  # noqa: E712
            .all()
        )
        for event in events:
            if not isinstance(event.data, dict):
                continue
            if str(event.data.get("meal_group_id")) != meal_group_id:
                continue

            data = dict(event.data)
            data.pop("total_calories", None)
            data.pop("total_carbs", None)
            data.pop("total_protein", None)
            data.pop("total_fat", None)
            event.data = data

        db.commit()

    delete_response = client.delete(f"/nutrition/meals/{meal_group_id}", headers=headers)
    assert delete_response.status_code == 200

    after_delete = client.get("/nutrition/macros", headers=headers)
    assert after_delete.status_code == 200
    after_data = after_delete.json()

    assert after_data["total_calories"] == 0
    assert after_data["carbs"] == 0
    assert after_data["protein"] == 0
    assert after_data["fat"] == 0
