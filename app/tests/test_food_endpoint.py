from typing import Any

from fastapi.testclient import TestClient
from pytest import MonkeyPatch


def test_parse_and_calculate_returns_calories_and_macros(client: TestClient, monkeypatch: MonkeyPatch) -> None:
    from app.schemas.food import ParsedFoodPayload
    from app.services.usda_service import USDAFoodResult

    def fake_parse_food_input(_text: str):
        return [ParsedFoodPayload(name="grilled chicken breast", quantity=200, unit="grams")]

    def fake_search_food_by_name(_normalized_name: str):
        return USDAFoodResult(
            fdc_id="12345",
            description="Chicken breast, grilled",
            calories_per_100g=135.0,
            carbs_per_100g=0.0,
            protein_per_100g=29.0,
            fat_per_100g=3.0,
            serving_size_grams=100.0,
        )

    monkeypatch.setattr("app.services.food_service.parse_food_input", fake_parse_food_input)
    monkeypatch.setattr("app.services.food_service.search_food_by_name", fake_search_food_by_name)

    response = client.post(
        "/api/food/parse-and-calculate",
        json={"text": "200 gramos de pechuga de pollo a la plancha"},
    )

    assert response.status_code == 200
    data: dict[str, Any] = response.json()

    assert data["food"] == "grilled chicken breast"
    assert data["quantity_grams"] == 200.0

    assert data["calories_per_100g"] == 135.0
    assert data["carbs_per_100g"] == 0.0
    assert data["protein_per_100g"] == 29.0
    assert data["fat_per_100g"] == 3.0

    assert data["total_calories"] == 270.0
    assert data["total_carbs"] == 0.0
    assert data["total_protein"] == 58.0
    assert data["total_fat"] == 6.0


def test_parse_and_calculate_serving_uses_serving_size_for_macro_totals(client: TestClient, monkeypatch: MonkeyPatch) -> None:
    from app.schemas.food import ParsedFoodPayload
    from app.services.usda_service import USDAFoodResult

    def fake_parse_food_input(_text: str):
        return [ParsedFoodPayload(name="cooked rice", quantity=2, unit="serving")]

    def fake_search_food_by_name(_normalized_name: str):
        return USDAFoodResult(
            fdc_id="67890",
            description="Rice, cooked",
            calories_per_100g=101.0,
            carbs_per_100g=22.0,
            protein_per_100g=2.4,
            fat_per_100g=0.3,
            serving_size_grams=120.0,
        )

    monkeypatch.setattr("app.services.food_service.parse_food_input", fake_parse_food_input)
    monkeypatch.setattr("app.services.food_service.search_food_by_name", fake_search_food_by_name)

    response = client.post(
        "/api/food/parse-and-calculate",
        json={"text": "2 porciones de arroz cocido"},
    )

    assert response.status_code == 200
    data: dict[str, Any] = response.json()

    assert data["quantity_grams"] == 240.0
    assert data["total_calories"] == 242.4
    assert data["total_carbs"] == 52.8
    assert data["total_protein"] == 5.76
    assert data["total_fat"] == 0.72


def test_parse_and_calculate_aggregates_multiple_foods(client: TestClient, monkeypatch: MonkeyPatch) -> None:
    from app.schemas.food import ParsedFoodPayload
    from app.services.usda_service import USDAFoodResult

    def fake_parse_food_input(_text: str):
        return [
            ParsedFoodPayload(name="chicken breast", quantity=100, unit="grams"),
            ParsedFoodPayload(name="cooked rice", quantity=200, unit="grams"),
        ]

    def fake_search_food_by_name(normalized_name: str):
        if normalized_name == "chicken breast":
            return USDAFoodResult(
                fdc_id="111",
                description="Chicken breast",
                calories_per_100g=165.0,
                carbs_per_100g=0.0,
                protein_per_100g=31.0,
                fat_per_100g=3.6,
                serving_size_grams=100.0,
            )

        return USDAFoodResult(
            fdc_id="222",
            description="Cooked rice",
            calories_per_100g=130.0,
            carbs_per_100g=28.0,
            protein_per_100g=2.7,
            fat_per_100g=0.3,
            serving_size_grams=100.0,
        )

    monkeypatch.setattr("app.services.food_service.parse_food_input", fake_parse_food_input)
    monkeypatch.setattr("app.services.food_service.search_food_by_name", fake_search_food_by_name)

    response = client.post(
        "/api/food/parse-and-calculate",
        json={"text": "pollo 100 gramos y arroz 200 gramos"},
    )

    assert response.status_code == 200
    data: dict[str, Any] = response.json()

    assert data["food"] == "chicken breast + cooked rice"
    assert data["quantity_grams"] == 300.0
    assert data["total_calories"] == 425.0
    assert data["total_carbs"] == 56.0
    assert data["total_protein"] == 36.4
    assert data["total_fat"] == 4.2


def test_parse_and_calculate_accepts_longer_input_text(client: TestClient, monkeypatch: MonkeyPatch) -> None:
    from app.schemas.food import ParsedFoodPayload
    from app.services.usda_service import USDAFoodResult

    def fake_parse_food_input(_text: str):
        return [ParsedFoodPayload(name="oatmeal", quantity=100, unit="grams")]

    def fake_search_food_by_name(_normalized_name: str):
        return USDAFoodResult(
            fdc_id="333",
            description="Oatmeal",
            calories_per_100g=68.0,
            carbs_per_100g=12.0,
            protein_per_100g=2.4,
            fat_per_100g=1.4,
            serving_size_grams=100.0,
        )

    monkeypatch.setattr("app.services.food_service.parse_food_input", fake_parse_food_input)
    monkeypatch.setattr("app.services.food_service.search_food_by_name", fake_search_food_by_name)

    long_text = " ".join(["avena con fruta y yogurt"] * 35)  # >500 chars

    response = client.post(
        "/api/food/parse-and-calculate",
        json={"text": long_text},
    )

    assert response.status_code == 200
    data: dict[str, Any] = response.json()
    assert data["food"] == "oatmeal"


def test_parse_and_calculate_decomposes_coffee_with_milk_and_uses_half_cups(client: TestClient, monkeypatch: MonkeyPatch) -> None:
    from app.schemas.food import ParsedFoodPayload
    from app.services.usda_service import USDAFoodResult

    def fake_parse_food_input(_text: str):
        return [
            ParsedFoodPayload(name="coffee", quantity=0.5, unit="cup"),
            ParsedFoodPayload(name="milk", quantity=0.5, unit="cup"),
        ]

    def fake_search_food_by_name(normalized_name: str):
        if normalized_name == "coffee":
            return USDAFoodResult(
                fdc_id="coffee-1",
                description="Brewed coffee",
                calories_per_100g=1.0,
                carbs_per_100g=0.0,
                protein_per_100g=0.1,
                fat_per_100g=0.0,
                serving_size_grams=240.0,
            )

        return USDAFoodResult(
            fdc_id="milk-1",
            description="Whole milk",
            calories_per_100g=61.0,
            carbs_per_100g=4.8,
            protein_per_100g=3.2,
            fat_per_100g=3.3,
            serving_size_grams=244.0,
        )

    monkeypatch.setattr("app.services.food_service.parse_food_input", fake_parse_food_input)
    monkeypatch.setattr("app.services.food_service.search_food_by_name", fake_search_food_by_name)

    response = client.post(
        "/api/food/parse-and-calculate",
        json={"text": "cafe con leche"},
    )

    assert response.status_code == 200
    data: dict[str, Any] = response.json()

    assert data["food"] == "coffee + milk"
    assert data["quantity_grams"] == 242.0
    assert data["total_calories"] > 70
    assert data["total_carbs"] > 5
