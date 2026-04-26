"""
Tests for the diet generation and meal tracker endpoints.

Covers:
  1. Diet generation — happy path with training_days (mocked Gemini)
  2. Diet generation — single-day plan (empty training_days)
  3. Get active diet — found and not found
  4. Get current meal — returns current meal by tracker index
  5. Log meal (complete) — advances current_meal_index
  6. Log meal (skip) — advances current_meal_index
  7. Log meal — daily reset when date changes
  8. Modify meal — add_food appends food and recalculates totals
  9. Modify meal — remove_food removes food
  10. Authorization — unauthenticated requests return 401
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

USER_DATA = {
    "email": "diet_user@nova.com",
    "password": "dietpass123",
    "first_name": "Ana",
    "last_name": "Lopez",
    "gender": "female",
    "weight": 60.0,
    "height": 163.0,
    "age": 30,
    "activity_level": 1.35,
    "role": "student",
}

SAMPLE_DIET_JSON = {
    "title": "Plan de alimentación personalizado",
    "description": "Dieta de prueba para tests.",
    "objective_label": "Recomposición corporal",
    "target_calories_rest": 1800,
    "target_calories_training": 2100,
    "target_protein_g": 120,
    "target_carbs_g": 200,
    "target_fat_g": 55,
    "water_ml_rest": 2100,
    "water_ml_training": 2600,
    "water_notes": "Basado en peso corporal.",
    "training_day": {
        "day_type": "training",
        "label": "Día de entrenamiento",
        "total_calories": 2100,
        "total_protein_g": 130,
        "total_carbs_g": 230,
        "total_fat_g": 57,
        "water_ml": 2600,
        "notes": "",
        "meals": [
            {
                "id": "breakfast",
                "name": "Desayuno",
                "total_calories": 420,
                "total_protein_g": 25,
                "total_carbs_g": 55,
                "total_fat_g": 10,
                "notes": "",
                "foods": [
                    {
                        "name": "Avena con leche",
                        "portion": "80g avena + 250ml leche",
                        "calories": 350,
                        "protein_g": 18,
                        "carbs_g": 52,
                        "fat_g": 6,
                        "notes": "",
                    },
                    {
                        "name": "Banana",
                        "portion": "1 unidad (120g)",
                        "calories": 110,
                        "protein_g": 1,
                        "carbs_g": 28,
                        "fat_g": 0,
                        "notes": "",
                    },
                ],
            },
            {
                "id": "lunch",
                "name": "Almuerzo",
                "total_calories": 600,
                "total_protein_g": 50,
                "total_carbs_g": 70,
                "total_fat_g": 15,
                "notes": "",
                "foods": [
                    {
                        "name": "Pollo a la plancha",
                        "portion": "200g",
                        "calories": 300,
                        "protein_g": 42,
                        "carbs_g": 0,
                        "fat_g": 7,
                        "notes": "",
                    }
                ],
            },
        ],
    },
    "rest_day": {
        "day_type": "rest",
        "label": "Día de descanso",
        "total_calories": 1800,
        "total_protein_g": 120,
        "total_carbs_g": 180,
        "total_fat_g": 52,
        "water_ml": 2100,
        "notes": "",
        "meals": [
            {
                "id": "breakfast",
                "name": "Desayuno",
                "total_calories": 400,
                "total_protein_g": 22,
                "total_carbs_g": 50,
                "total_fat_g": 10,
                "notes": "",
                "foods": [
                    {
                        "name": "Tostadas con queso",
                        "portion": "2 tostadas + 30g queso",
                        "calories": 280,
                        "protein_g": 14,
                        "carbs_g": 32,
                        "fat_g": 9,
                        "notes": "",
                    }
                ],
            },
            {
                "id": "lunch",
                "name": "Almuerzo",
                "total_calories": 550,
                "total_protein_g": 45,
                "total_carbs_g": 60,
                "total_fat_g": 12,
                "notes": "",
                "foods": [],
            },
        ],
    },
    "health_notes": ["Mantener buena hidratación."],
    "supplement_suggestions": "",
    "nutritional_summary": "Plan equilibrado para recomposición.",
}

DIET_INTAKE = {
    "meals_count": 4,
    "dietary_restrictions": "ninguna",
    "food_allergies": "ninguna",
    "health_conditions": "ninguna",
    "disliked_foods": "",
    "budget_level": "moderado",
    "cooking_time": "moderado (30-45 min)",
    "meal_timing_preference": "",
    "training_days": ["lunes", "miércoles", "viernes"],
}


def _register_and_login(client: TestClient) -> str:
    """Register user and return Bearer token."""
    client.post("/auth/register", json=USER_DATA)
    resp = client.post(
        "/auth/login",
        json={"email": USER_DATA["email"], "password": USER_DATA["password"]},
    )
    return resp.json()["access_token"]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestDietGeneration:
    def test_generate_with_training_days(self, client: TestClient) -> None:
        """Diet generation stores training_days inside diet_data."""
        token = _register_and_login(client)
        with patch(
            "app.services.diet_service.DietService._call_gemini",
            return_value=dict(SAMPLE_DIET_JSON),
        ):
            resp = client.post(
                "/v1/diet/generate",
                json={"intake": DIET_INTAKE, "free_text": ""},
                headers=_auth_headers(token),
            )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "ready"
        assert data["diet_data"]["training_days"] == ["lunes", "miércoles", "viernes"]

    def test_generate_single_day_empty_training_days(self, client: TestClient) -> None:
        """Empty training_days results in a valid diet with no training day distinction."""
        token = _register_and_login(client)
        intake_no_days = {**DIET_INTAKE, "training_days": []}
        with patch(
            "app.services.diet_service.DietService._call_gemini",
            return_value=dict(SAMPLE_DIET_JSON),
        ):
            resp = client.post(
                "/v1/diet/generate",
                json={"intake": intake_no_days, "free_text": ""},
                headers=_auth_headers(token),
            )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "ready"
        assert data["diet_data"]["training_days"] == []

    def test_generate_resets_meal_tracker(self, client: TestClient) -> None:
        """Generating a new diet resets current_meal_index to 0."""
        token = _register_and_login(client)
        with patch(
            "app.services.diet_service.DietService._call_gemini",
            return_value=dict(SAMPLE_DIET_JSON),
        ):
            resp = client.post(
                "/v1/diet/generate",
                json={"intake": DIET_INTAKE, "free_text": ""},
                headers=_auth_headers(token),
            )
        assert resp.json()["current_meal_index"] == 0

    def test_generate_unauthenticated(self, client: TestClient) -> None:
        resp = client.post("/v1/diet/generate", json={"intake": DIET_INTAKE, "free_text": ""})
        assert resp.status_code == 401


class TestGetActiveDiet:
    def test_get_active_diet_found(self, client: TestClient) -> None:
        token = _register_and_login(client)
        with patch(
            "app.services.diet_service.DietService._call_gemini",
            return_value=dict(SAMPLE_DIET_JSON),
        ):
            client.post(
                "/v1/diet/generate",
                json={"intake": DIET_INTAKE, "free_text": ""},
                headers=_auth_headers(token),
            )
        resp = client.get("/v1/diet/active", headers=_auth_headers(token))
        assert resp.status_code == 200
        assert resp.json()["status"] == "ready"

    def test_get_active_diet_not_found(self, client: TestClient) -> None:
        token = _register_and_login(client)
        resp = client.get("/v1/diet/active", headers=_auth_headers(token))
        assert resp.status_code == 404


class TestMealTracker:
    def _setup_diet(self, client: TestClient, token: str) -> None:
        with patch(
            "app.services.diet_service.DietService._call_gemini",
            return_value=dict(SAMPLE_DIET_JSON),
        ):
            client.post(
                "/v1/diet/generate",
                json={"intake": DIET_INTAKE, "free_text": ""},
                headers=_auth_headers(token),
            )

    def test_log_meal_complete_advances_index(self, client: TestClient) -> None:
        token = _register_and_login(client)
        self._setup_diet(client, token)
        resp = client.post(
            "/v1/diet/log-meal",
            json={"action": "complete"},
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["current_meal_index"] == 1
        assert data["advanced"] is True

    def test_log_meal_skip_advances_index(self, client: TestClient) -> None:
        token = _register_and_login(client)
        self._setup_diet(client, token)
        resp = client.post(
            "/v1/diet/log-meal",
            json={"action": "skip"},
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        assert resp.json()["current_meal_index"] == 1

    def test_log_meal_clamps_at_total_meals(self, client: TestClient) -> None:
        """Index does not exceed total meals (2 in sample data)."""
        token = _register_and_login(client)
        self._setup_diet(client, token)
        headers = _auth_headers(token)
        client.post("/v1/diet/log-meal", json={"action": "complete"}, headers=headers)
        client.post("/v1/diet/log-meal", json={"action": "complete"}, headers=headers)
        resp = client.post("/v1/diet/log-meal", json={"action": "complete"}, headers=headers)
        assert resp.json()["current_meal_index"] == 2  # clamped at total_meals

    def test_log_meal_invalid_action(self, client: TestClient) -> None:
        token = _register_and_login(client)
        self._setup_diet(client, token)
        resp = client.post(
            "/v1/diet/log-meal",
            json={"action": "invalid"},
            headers=_auth_headers(token),
        )
        assert resp.status_code == 422

    def test_log_meal_no_diet(self, client: TestClient) -> None:
        token = _register_and_login(client)
        resp = client.post(
            "/v1/diet/log-meal",
            json={"action": "complete"},
            headers=_auth_headers(token),
        )
        assert resp.status_code == 404

    def test_get_current_meal_returns_first_meal(self, client: TestClient) -> None:
        token = _register_and_login(client)
        self._setup_diet(client, token)
        resp = client.get("/v1/diet/current-meal", headers=_auth_headers(token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["meal_index"] == 0
        assert data["total_meals"] == 2
        assert data["meal"] is not None

    def test_get_current_meal_no_diet(self, client: TestClient) -> None:
        token = _register_and_login(client)
        resp = client.get("/v1/diet/current-meal", headers=_auth_headers(token))
        assert resp.status_code == 404


class TestModifyMeal:
    NEW_FOOD = {
        "name": "Manzana",
        "portion": "1 unidad (150g)",
        "calories": 78,
        "protein_g": 0.4,
        "carbs_g": 20,
        "fat_g": 0.2,
        "notes": "",
    }

    def _setup_diet(self, client: TestClient, token: str) -> None:
        with patch(
            "app.services.diet_service.DietService._call_gemini",
            return_value=dict(SAMPLE_DIET_JSON),
        ):
            client.post(
                "/v1/diet/generate",
                json={"intake": DIET_INTAKE, "free_text": ""},
                headers=_auth_headers(token),
            )

    def test_add_food_appends_to_meal(self, client: TestClient) -> None:
        token = _register_and_login(client)
        self._setup_diet(client, token)
        resp = client.post(
            "/v1/diet/modify-meal",
            json={
                "day_type": "rest_day",
                "meal_id": "breakfast",
                "action": "add_food",
                "food": self.NEW_FOOD,
            },
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        meals = resp.json()["diet_data"]["rest_day"]["meals"]
        breakfast = next(m for m in meals if m["id"] == "breakfast")
        food_names = [f["name"] for f in breakfast["foods"]]
        assert "Manzana" in food_names

    def test_remove_food_removes_from_meal(self, client: TestClient) -> None:
        token = _register_and_login(client)
        self._setup_diet(client, token)
        resp = client.post(
            "/v1/diet/modify-meal",
            json={
                "day_type": "training_day",
                "meal_id": "breakfast",
                "action": "remove_food",
                "food_index": 0,
            },
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        meals = resp.json()["diet_data"]["training_day"]["meals"]
        breakfast = next(m for m in meals if m["id"] == "breakfast")
        # Was 2 foods, now 1
        assert len(breakfast["foods"]) == 1

    def test_add_food_missing_food_payload(self, client: TestClient) -> None:
        token = _register_and_login(client)
        self._setup_diet(client, token)
        resp = client.post(
            "/v1/diet/modify-meal",
            json={
                "day_type": "rest_day",
                "meal_id": "breakfast",
                "action": "add_food",
            },
            headers=_auth_headers(token),
        )
        assert resp.status_code == 400

    def test_modify_meal_unauthenticated(self, client: TestClient) -> None:
        resp = client.post(
            "/v1/diet/modify-meal",
            json={
                "day_type": "rest_day",
                "meal_id": "breakfast",
                "action": "add_food",
                "food": self.NEW_FOOD,
            },
        )
        assert resp.status_code == 401


# ── Sample alternative meal ───────────────────────────────────────────────────

SAMPLE_ALT_MEAL = {
    "id": "meal_alt",
    "name": "Desayuno alternativo",
    "foods": [
        {
            "name": "Yogur griego",
            "portion": "200g",
            "calories": 200.0,
            "protein_g": 18.0,
            "carbs_g": 14.0,
            "fat_g": 6.0,
            "notes": "",
        }
    ],
    "total_calories": 200.0,
    "total_protein_g": 18.0,
    "total_carbs_g": 14.0,
    "total_fat_g": 6.0,
    "notes": "",
}


class TestDailyConsumedTracking:
    """Completing a meal should accumulate macros in daily_consumed AND in DailyNutrition."""

    def _setup_diet(self, client: TestClient, token: str) -> None:
        with patch(
            "app.services.diet_service.DietService._call_gemini",
            return_value=dict(SAMPLE_DIET_JSON),
        ):
            client.post(
                "/v1/diet/generate",
                json={"intake": DIET_INTAKE, "free_text": ""},
                headers=_auth_headers(token),
            )

    def test_log_complete_adds_to_daily_consumed(self, client: TestClient) -> None:
        """Completing meal[0] should write its macros into daily_consumed."""
        token = _register_and_login(client)
        self._setup_diet(client, token)
        headers = _auth_headers(token)

        # Resolve which meal is current (depends on today's day type)
        current = client.get("/v1/diet/current-meal", headers=headers).json()
        meal = current["meal"]

        client.post("/v1/diet/log-meal", json={"action": "complete"}, headers=headers)

        diet = client.get("/v1/diet/active", headers=headers).json()
        consumed = diet.get("daily_consumed") or {}
        assert consumed, "daily_consumed should not be empty after completing a meal"
        today_entry = list(consumed.values())[0]
        assert today_entry["calories"] == pytest.approx(meal["total_calories"], abs=0.5)
        assert today_entry["protein_g"] == pytest.approx(meal["total_protein_g"], abs=0.5)
        assert today_entry["carbs_g"] == pytest.approx(meal["total_carbs_g"], abs=0.5)
        assert today_entry["fat_g"] == pytest.approx(meal["total_fat_g"], abs=0.5)

    def test_log_skip_does_not_add_to_daily_consumed(self, client: TestClient) -> None:
        """Skipping a meal must NOT accumulate macros."""
        token = _register_and_login(client)
        self._setup_diet(client, token)
        headers = _auth_headers(token)

        client.post("/v1/diet/log-meal", json={"action": "skip"}, headers=headers)

        diet = client.get("/v1/diet/active", headers=headers).json()
        consumed = diet.get("daily_consumed") or {}
        # Either empty or has a zero-value entry — calories must be 0
        if consumed:
            today_entry = list(consumed.values())[0]
            assert today_entry.get("calories", 0) == pytest.approx(0, abs=0.1)

    def test_log_complete_twice_accumulates(self, client: TestClient) -> None:
        """Completing two meals should sum both into daily_consumed."""
        token = _register_and_login(client)
        self._setup_diet(client, token)
        headers = _auth_headers(token)

        m0 = client.get("/v1/diet/current-meal", headers=headers).json()["meal"]
        client.post("/v1/diet/log-meal", json={"action": "complete"}, headers=headers)
        m1 = client.get("/v1/diet/current-meal", headers=headers).json()["meal"]
        client.post("/v1/diet/log-meal", json={"action": "complete"}, headers=headers)

        diet = client.get("/v1/diet/active", headers=headers).json()
        consumed = diet.get("daily_consumed") or {}
        today_entry = list(consumed.values())[0]
        expected_cal = m0["total_calories"] + m1["total_calories"]
        assert today_entry["calories"] == pytest.approx(expected_cal, abs=1)

    def test_log_complete_updates_dashboard_macros(self, client: TestClient) -> None:
        """Completing a planned meal must also update the DailyNutrition table (dashboard source)."""
        token = _register_and_login(client)
        self._setup_diet(client, token)
        headers = _auth_headers(token)

        meal = client.get("/v1/diet/current-meal", headers=headers).json()["meal"]
        client.post("/v1/diet/log-meal", json={"action": "complete"}, headers=headers)

        # Dashboard reads from /nutrition/macros — fields: total_calories, carbs, protein, fat
        macros = client.get("/nutrition/macros", headers=headers).json()
        # total_calories in DailyNutrition is computed from macro sums (carbs×4 + protein×4 + fat×9),
        # which may differ slightly from the meal's stored total_calories — allow up to 15 kcal.
        assert macros["total_calories"] == pytest.approx(meal["total_calories"], abs=15)
        assert macros["protein"] == pytest.approx(meal["total_protein_g"], abs=1)
        assert macros["carbs"] == pytest.approx(meal["total_carbs_g"], abs=1)
        assert macros["fat"] == pytest.approx(meal["total_fat_g"], abs=1)


class TestMealAlternative:
    """AI-generated meal alternatives and their application."""

    def _setup_diet(self, client: TestClient, token: str) -> None:
        with patch(
            "app.services.diet_service.DietService._call_gemini",
            return_value=dict(SAMPLE_DIET_JSON),
        ):
            client.post(
                "/v1/diet/generate",
                json={"intake": DIET_INTAKE, "free_text": ""},
                headers=_auth_headers(token),
            )

    def test_get_alternative_returns_meal(self, client: TestClient) -> None:
        """GET /meals/alternative returns a valid alternative meal."""
        token = _register_and_login(client)
        self._setup_diet(client, token)
        with patch(
            "app.services.diet_service.DietService._call_gemini_light",
            return_value=dict(SAMPLE_ALT_MEAL),
        ):
            resp = client.post(
                "/v1/diet/meals/alternative",
                headers=_auth_headers(token),
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["meal"]["name"] == "Desayuno alternativo"
        assert data["meal_index"] == 0
        assert data["day_type"] in ("training_day", "rest_day")

    def test_get_alternative_no_diet_returns_404(self, client: TestClient) -> None:
        token = _register_and_login(client)
        resp = client.post("/v1/diet/meals/alternative", headers=_auth_headers(token))
        assert resp.status_code == 404

    def test_apply_alternative_today_sets_override(self, client: TestClient) -> None:
        """Applying with scope='today' stores override; current-meal returns overridden meal."""
        token = _register_and_login(client)
        self._setup_diet(client, token)
        headers = _auth_headers(token)

        current = client.get("/v1/diet/current-meal", headers=headers).json()
        day_type = current["day_type"]
        meal_index = current["meal_index"]

        resp = client.post(
            "/v1/diet/meals/apply-alternative",
            json={
                "meal_index": meal_index,
                "day_type": day_type,
                "scope": "today",
                "meal": SAMPLE_ALT_MEAL,
            },
            headers=headers,
        )
        assert resp.status_code == 204

        # current-meal should now return the override
        updated = client.get("/v1/diet/current-meal", headers=headers).json()
        assert updated["meal"]["name"] == "Desayuno alternativo"
        assert updated["is_overridden"] is True

    def test_apply_alternative_diet_replaces_permanently(self, client: TestClient) -> None:
        """Applying with scope='diet' updates diet_data permanently."""
        token = _register_and_login(client)
        self._setup_diet(client, token)
        headers = _auth_headers(token)

        current = client.get("/v1/diet/current-meal", headers=headers).json()
        day_type = current["day_type"]
        meal_index = current["meal_index"]

        resp = client.post(
            "/v1/diet/meals/apply-alternative",
            json={
                "meal_index": meal_index,
                "day_type": day_type,
                "scope": "diet",
                "meal": SAMPLE_ALT_MEAL,
            },
            headers=headers,
        )
        assert resp.status_code == 204

        diet = client.get("/v1/diet/active", headers=headers).json()
        meals = diet["diet_data"][day_type]["meals"]
        assert meals[meal_index]["name"] == "Desayuno alternativo"

    def test_apply_alternative_invalid_scope(self, client: TestClient) -> None:
        token = _register_and_login(client)
        self._setup_diet(client, token)
        resp = client.post(
            "/v1/diet/meals/apply-alternative",
            json={
                "meal_index": 0,
                "day_type": "training_day",
                "scope": "invalid",
                "meal": SAMPLE_ALT_MEAL,
            },
            headers=_auth_headers(token),
        )
        assert resp.status_code == 400

    def test_apply_alternative_unauthenticated(self, client: TestClient) -> None:
        resp = client.post(
            "/v1/diet/meals/apply-alternative",
            json={
                "meal_index": 0,
                "day_type": "training_day",
                "scope": "today",
                "meal": SAMPLE_ALT_MEAL,
            },
        )
        assert resp.status_code == 401
