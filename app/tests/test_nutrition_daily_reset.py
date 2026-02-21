from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.config import settings


def _get_auth_header(client, test_user_data):
    client.post("/auth/register", json=test_user_data)
    login_response = client.post(
        "/auth/login",
        json={"email": test_user_data["email"], "password": test_user_data["password"]},
    )
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_daily_nutrition_resets_next_day_but_previous_day_persists(client, test_user_data):
    headers = _get_auth_header(client, test_user_data)

    meal_payload = {
        "meal_type": "meal",
        "food_name": "arroz integral cocido",
        "quantity_grams": 100,
        "calories_per_100g": 124,
        "carbs_per_100g": 25.9,
        "protein_per_100g": 2.4,
        "fat_per_100g": 1.1,
    }

    log_response = client.post("/nutrition/meals", json=meal_payload, headers=headers)
    assert log_response.status_code == 200

    try:
        app_tz = ZoneInfo(settings.APP_TIMEZONE)
    except ZoneInfoNotFoundError:
        app_tz = timezone.utc

    event_timestamp_raw = log_response.json()["event_timestamp"]
    event_timestamp = datetime.fromisoformat(event_timestamp_raw.replace("Z", "+00:00"))
    today = event_timestamp.astimezone(app_tz).date()
    tomorrow = today + timedelta(days=1)

    today_response = client.get(f"/nutrition/macros?target_date={today.isoformat()}", headers=headers)
    assert today_response.status_code == 200
    today_data = today_response.json()
    assert today_data["total_calories"] > 0
    assert today_data["carbs"] > 0

    tomorrow_response = client.get(f"/nutrition/macros?target_date={tomorrow.isoformat()}", headers=headers)
    assert tomorrow_response.status_code == 200
    tomorrow_data = tomorrow_response.json()
    assert tomorrow_data["total_calories"] == 0
    assert tomorrow_data["carbs"] == 0
    assert tomorrow_data["protein"] == 0
    assert tomorrow_data["fat"] == 0

    # Previous day remains persisted and retrievable for future reports.
    previous_day_response = client.get(f"/nutrition/macros?target_date={today.isoformat()}", headers=headers)
    assert previous_day_response.status_code == 200
    previous_day_data = previous_day_response.json()
    assert previous_day_data["total_calories"] == today_data["total_calories"]
    assert previous_day_data["carbs"] == today_data["carbs"]
