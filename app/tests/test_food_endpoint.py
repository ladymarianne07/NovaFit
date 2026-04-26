from typing import Any

from fastapi.testclient import TestClient
from pytest import MonkeyPatch


def test_parse_and_calculate_prefers_fatsecret_before_usda(authed_client: TestClient, monkeypatch: MonkeyPatch) -> None:
    from app.schemas.food import ParsedFoodPayload
    from app.services.fatsecret_service import FatSecretFoodResult

    def fake_parse_food_input(_text: str):
        return [ParsedFoodPayload(name="banana", quantity=100, unit="grams")]

    def fake_fatsecret_search(_normalized_name: str):
        return FatSecretFoodResult(
            food_id="fs-123",
            description="Banana",
            calories_per_100g=89.0,
            carbs_per_100g=22.8,
            protein_per_100g=1.1,
            fat_per_100g=0.3,
            serving_size_grams=None,
        )

    def fake_usda_search(_normalized_name: str):
        raise AssertionError("USDA should not be called when FatSecret already resolved the food")

    monkeypatch.setattr("app.services.food_service.parse_food_input", fake_parse_food_input)
    monkeypatch.setattr("app.services.food_service.search_fatsecret_food_by_name", fake_fatsecret_search)
    monkeypatch.setattr("app.services.food_service.search_food_by_name", fake_usda_search)

    response = authed_client.post(
        "/api/food/parse-and-calculate",
        json={"text": "100 gramos de banana"},
    )

    assert response.status_code == 200
    data: dict[str, Any] = response.json()

    assert data["food"] == "banana"
    assert data["calories_per_100g"] == 89.0
    assert data["total_calories"] == 89.0


def test_parse_and_calculate_falls_back_to_usda_when_fatsecret_fails(
    authed_client: TestClient,
    monkeypatch: MonkeyPatch,
) -> None:
    from app.schemas.food import ParsedFoodPayload
    from app.services.fatsecret_service import FatSecretServiceError
    from app.services.usda_service import USDAFoodResult

    def fake_parse_food_input(_text: str):
        return [ParsedFoodPayload(name="banana", quantity=100, unit="grams")]

    def fake_fatsecret_search(_normalized_name: str):
        raise FatSecretServiceError("food_not_found")

    def fake_usda_search(_normalized_name: str):
        return USDAFoodResult(
            fdc_id="09040",
            description="Bananas, raw",
            calories_per_100g=88.0,
            carbs_per_100g=22.8,
            protein_per_100g=1.1,
            fat_per_100g=0.3,
            serving_size_grams=100.0,
        )

    monkeypatch.setattr("app.services.food_service.parse_food_input", fake_parse_food_input)
    monkeypatch.setattr("app.services.food_service.search_fatsecret_food_by_name", fake_fatsecret_search)
    monkeypatch.setattr("app.services.food_service.search_food_by_name", fake_usda_search)

    response = authed_client.post(
        "/api/food/parse-and-calculate",
        json={"text": "100 gramos de banana"},
    )

    assert response.status_code == 200
    data: dict[str, Any] = response.json()
    assert data["food"] == "banana"
    assert data["calories_per_100g"] == 88.0
    assert data["total_calories"] == 88.0


def test_parse_and_calculate_uses_parser_pipeline_without_fatsecret_nlp(authed_client: TestClient, monkeypatch: MonkeyPatch) -> None:
    from app.schemas.food import ParsedFoodPayload
    from app.services.usda_service import USDAFoodResult

    def fake_parse_food_input(_text: str):
        return [ParsedFoodPayload(name="banana", quantity=118, unit="grams")]

    def fake_usda_search(_normalized_name: str):
        return USDAFoodResult(
            fdc_id="09040",
            description="Bananas, raw",
            calories_per_100g=88.0,
            carbs_per_100g=22.8,
            protein_per_100g=1.1,
            fat_per_100g=0.3,
            serving_size_grams=100.0,
        )

    monkeypatch.setattr("app.services.food_service.parse_food_input", fake_parse_food_input)
    monkeypatch.setattr("app.services.food_service.search_food_by_name", fake_usda_search)

    response = authed_client.post(
        "/api/food/parse-and-calculate",
        json={"text": "me comi una banana mediana"},
    )

    assert response.status_code == 200
    data: dict[str, Any] = response.json()
    assert data["food"] == "banana"
    assert data["quantity_grams"] == 118.0
    assert data["total_calories"] == 103.84


def test_parse_and_calculate_returns_calories_and_macros(authed_client: TestClient, monkeypatch: MonkeyPatch) -> None:
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

    response = authed_client.post(
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


def test_parse_and_calculate_serving_uses_serving_size_for_macro_totals(authed_client: TestClient, monkeypatch: MonkeyPatch) -> None:
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

    response = authed_client.post(
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


def test_parse_and_calculate_aggregates_multiple_foods(authed_client: TestClient, monkeypatch: MonkeyPatch) -> None:
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

    response = authed_client.post(
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


def test_parse_and_calculate_accepts_longer_input_text(authed_client: TestClient, monkeypatch: MonkeyPatch) -> None:
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

    response = authed_client.post(
        "/api/food/parse-and-calculate",
        json={"text": long_text},
    )

    assert response.status_code == 200
    data: dict[str, Any] = response.json()
    assert data["food"] == "oatmeal"


def test_parse_and_calculate_decomposes_coffee_with_milk_and_uses_half_cups(authed_client: TestClient, monkeypatch: MonkeyPatch) -> None:
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

    response = authed_client.post(
        "/api/food/parse-and-calculate",
        json={"text": "cafe con leche"},
    )

    assert response.status_code == 200
    data: dict[str, Any] = response.json()

    assert data["food"] == "coffee + milk"
    assert data["quantity_grams"] == 242.0
    assert data["total_calories"] > 70
    assert data["total_carbs"] > 5


def test_parse_and_calculate_applies_conservative_defaults_for_ambiguous_breakfast(
    authed_client: TestClient,
    monkeypatch: MonkeyPatch,
) -> None:
    from app.schemas.food import ParsedFoodPayload
    from app.services.fatsecret_service import FatSecretFoodResult

    def fake_parse_food_input(_text: str):
        return [
            ParsedFoodPayload(name="sweetener", quantity=1, unit="serving"),
            ParsedFoodPayload(name="lactose-free milk", quantity=1, unit="serving"),
            ParsedFoodPayload(name="coffee", quantity=1, unit="serving"),
            ParsedFoodPayload(name="butter", quantity=1, unit="serving"),
            ParsedFoodPayload(name="scrambled eggs", quantity=2, unit="serving"),
            ParsedFoodPayload(name="whole wheat toast", quantity=1, unit="serving"),
        ]

    def fake_fatsecret_search(normalized_name: str):
        mapping = {
            "sweetener": FatSecretFoodResult(
                food_id="s-1",
                description="sweetener",
                calories_per_100g=0.0,
                carbs_per_100g=0.0,
                protein_per_100g=0.0,
                fat_per_100g=0.0,
                serving_size_grams=1.0,
            ),
            "lactose-free milk": FatSecretFoodResult(
                food_id="m-1",
                description="lactose free milk",
                calories_per_100g=48.0,
                carbs_per_100g=4.9,
                protein_per_100g=3.3,
                fat_per_100g=1.6,
                serving_size_grams=200.0,
            ),
            "coffee": FatSecretFoodResult(
                food_id="c-1",
                description="coffee",
                calories_per_100g=1.0,
                carbs_per_100g=0.0,
                protein_per_100g=0.1,
                fat_per_100g=0.0,
                serving_size_grams=240.0,
            ),
            "butter": FatSecretFoodResult(
                food_id="b-1",
                description="butter",
                calories_per_100g=717.0,
                carbs_per_100g=0.1,
                protein_per_100g=0.8,
                fat_per_100g=81.0,
                serving_size_grams=None,
            ),
            "egg": FatSecretFoodResult(
                food_id="e-1",
                description="egg",
                calories_per_100g=143.0,
                carbs_per_100g=0.7,
                protein_per_100g=12.6,
                fat_per_100g=9.5,
                serving_size_grams=50.0,
            ),
            "whole wheat toast": FatSecretFoodResult(
                food_id="t-1",
                description="whole wheat toast",
                calories_per_100g=265.0,
                carbs_per_100g=49.0,
                protein_per_100g=9.0,
                fat_per_100g=3.2,
                serving_size_grams=40.0,
            ),
        }
        if normalized_name not in mapping:
            raise AssertionError(f"unexpected lookup: {normalized_name}")
        return mapping[normalized_name]

    monkeypatch.setattr("app.services.food_service.parse_food_input", fake_parse_food_input)
    monkeypatch.setattr("app.services.food_service.search_fatsecret_food_by_name", fake_fatsecret_search)

    def fake_resolve_portion_grams(
        db: Any,
        food_name: str,
        unit: str,
        preferred_serving_grams: float | None = None,
    ) -> float:
        _ = db, preferred_serving_grams
        food_name = str(food_name).lower()
        unit = str(unit).lower()
        if food_name == "butter" and unit == "serving":
            return 108.0
        return 50.0

    monkeypatch.setattr("app.services.food_service.PortionResolverService.resolve_portion_grams", fake_resolve_portion_grams)

    response = authed_client.post(
        "/api/food/parse-and-calculate",
        json={"text": "sweetener, lactose-free milk, café, manteca, scrambled eggs, whole wheat toast"},
    )

    assert response.status_code == 200
    data: dict[str, Any] = response.json()

    # Conservative defaults should avoid inflated values near 800+ kcal.
    assert data["total_calories"] < 450.0
    assert data["total_protein"] < 30.0
    assert data["total_fat"] < 30.0


def test_parse_and_calculate_requires_auth(client: TestClient) -> None:
    """Trello card #4 — endpoint must reject anonymous requests."""
    response = client.post(
        "/api/food/parse-and-calculate",
        json={"text": "100 gramos de banana"},
    )
    assert response.status_code == 401


def test_search_multi_requires_auth(client: TestClient) -> None:
    """Trello card #4 — endpoint must reject anonymous requests."""
    response = client.get("/api/food/search-multi", params={"query": "banana"})
    assert response.status_code == 401
