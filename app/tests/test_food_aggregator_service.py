from __future__ import annotations

import pytest
from pytest import MonkeyPatch

from app.schemas.food_normalized import FoodNormalized
from app.services.connectors.base_connector import FoodConnector
import app.services.food_aggregator_service as aggregator_module
from app.services.food_aggregator_service import FoodAggregatorService


def _fake_exists_in_local_db(query: str, db: object | None) -> bool:
    _ = (query, db)
    return False


class FakeConnector(FoodConnector):
    def __init__(self, source_name: str, items: list[FoodNormalized]) -> None:
        self.source_name = source_name
        self._items = items

    async def search(self, query: str) -> list[FoodNormalized]:
        _ = query
        return self._items


@pytest.mark.asyncio
async def test_search_food_prioritizes_openfoodfacts_for_barcode(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(aggregator_module, "_exists_in_local_db", _fake_exists_in_local_db)

    service = FoodAggregatorService(
        connectors=[
            FakeConnector(
                "usda",
                [
                    FoodNormalized(
                        name="Tuna, canned",
                        brand=None,
                        calories_per_100g=116,
                        protein_per_100g=26,
                        fat_per_100g=1,
                        carbs_per_100g=0,
                        fiber_per_100g=None,
                        source="usda",
                        confidence_score=0.9,
                    )
                ],
            ),
            FakeConnector(
                "openfoodfacts",
                [
                    FoodNormalized(
                        name="Tuna Can 123",
                        brand="Acme",
                        calories_per_100g=120,
                        protein_per_100g=25,
                        fat_per_100g=2,
                        carbs_per_100g=0,
                        fiber_per_100g=0,
                        source="openfoodfacts",
                        confidence_score=0.85,
                    )
                ],
            ),
        ]
    )

    results = await service.search_food("7791234567890")

    assert results
    assert results[0].source == "openfoodfacts"


@pytest.mark.asyncio
async def test_search_food_prioritizes_usda_for_non_branded_query(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(aggregator_module, "_exists_in_local_db", _fake_exists_in_local_db)

    service = FoodAggregatorService(
        connectors=[
            FakeConnector(
                "usda",
                [
                    FoodNormalized(
                        name="Fish, baked",
                        brand=None,
                        calories_per_100g=128,
                        protein_per_100g=25,
                        fat_per_100g=3,
                        carbs_per_100g=0,
                        fiber_per_100g=None,
                        source="usda",
                        confidence_score=0.9,
                    )
                ],
            ),
            FakeConnector(
                "openfoodfacts",
                [
                    FoodNormalized(
                        name="Fish meal prep",
                        brand="FitBrand",
                        calories_per_100g=150,
                        protein_per_100g=20,
                        fat_per_100g=7,
                        carbs_per_100g=5,
                        fiber_per_100g=1,
                        source="openfoodfacts",
                        confidence_score=0.85,
                    )
                ],
            ),
        ]
    )

    results = await service.search_food("fish")

    assert results
    assert results[0].source == "usda"


@pytest.mark.asyncio
async def test_search_food_deduplicates_and_limits_top5(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(aggregator_module, "_exists_in_local_db", _fake_exists_in_local_db)

    duplicated = FoodNormalized(
        name="Chicken breast grilled",
        brand=None,
        calories_per_100g=165,
        protein_per_100g=31,
        fat_per_100g=3.6,
        carbs_per_100g=0,
        fiber_per_100g=None,
        source="usda",
        confidence_score=0.9,
    )

    items = [
        duplicated,
        duplicated.model_copy(update={"source": "openfoodfacts", "confidence_score": 0.86}),
        FoodNormalized(
            name="Rice cooked",
            brand=None,
            calories_per_100g=130,
            protein_per_100g=2.7,
            fat_per_100g=0.3,
            carbs_per_100g=28,
            fiber_per_100g=0.4,
            source="usda",
            confidence_score=0.88,
        ),
        FoodNormalized(
            name="Potato baked",
            brand=None,
            calories_per_100g=93,
            protein_per_100g=2.5,
            fat_per_100g=0.1,
            carbs_per_100g=21,
            fiber_per_100g=2.2,
            source="usda",
            confidence_score=0.87,
        ),
        FoodNormalized(
            name="Egg whole cooked",
            brand=None,
            calories_per_100g=155,
            protein_per_100g=13,
            fat_per_100g=11,
            carbs_per_100g=1.1,
            fiber_per_100g=0,
            source="usda",
            confidence_score=0.89,
        ),
        FoodNormalized(
            name="Milk whole",
            brand=None,
            calories_per_100g=61,
            protein_per_100g=3.2,
            fat_per_100g=3.3,
            carbs_per_100g=4.8,
            fiber_per_100g=0,
            source="usda",
            confidence_score=0.84,
        ),
        FoodNormalized(
            name="Coffee black",
            brand=None,
            calories_per_100g=1,
            protein_per_100g=0.1,
            fat_per_100g=0,
            carbs_per_100g=0,
            fiber_per_100g=0,
            source="usda",
            confidence_score=0.83,
        ),
    ]

    service = FoodAggregatorService(connectors=[FakeConnector("usda", items)])

    results = await service.search_food("comida")

    assert len(results) == 5
    names = [item.name for item in results]
    assert names.count("Chicken breast grilled") == 1
