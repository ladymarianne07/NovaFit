from __future__ import annotations

import logging
from typing import Any, cast

import httpx

from ...config import settings
from ...schemas.food_normalized import FoodNormalized
from .base_connector import FoodConnector, clamp_confidence


logger = logging.getLogger(__name__)

USDA_BASE_CONFIDENCE = 0.9
USDA_SEARCH_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"
USDA_TIMEOUT_SECONDS = 8.0


class USDAConnector(FoodConnector):
    """Connector for USDA FoodData Central search endpoint."""

    source_name = "usda"

    def __init__(self, timeout_seconds: float = USDA_TIMEOUT_SECONDS) -> None:
        self.timeout_seconds = timeout_seconds

    async def search(self, query: str) -> list[FoodNormalized]:
        if not settings.USDA_API_KEY:
            logger.warning("USDA API key missing; skipping USDA connector")
            return []

        payload: dict[str, Any] = {
            "query": query,
            "pageSize": 10,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    USDA_SEARCH_URL,
                    params={"api_key": settings.USDA_API_KEY},
                    json=payload,
                )
                response.raise_for_status()
        except httpx.TimeoutException:
            logger.warning("USDA connector timeout for query='%s'", query)
            return []
        except httpx.HTTPError as exc:
            logger.warning("USDA connector request failed for query='%s': %s", query, exc)
            return []

        data_raw: Any = response.json()
        if not isinstance(data_raw, dict):
            return []

        data = cast(dict[str, Any], data_raw)
        foods_raw = data.get("foods", [])
        if not isinstance(foods_raw, list):
            return []

        foods_list = cast(list[Any], foods_raw)

        normalized: list[FoodNormalized] = []
        for food in foods_list:
            if not isinstance(food, dict):
                continue
            food_dict = cast(dict[str, Any], food)

            description = str(food_dict.get("description", "")).strip()
            if not description:
                continue

            calories = _extract_kcal_per_100g(food_dict)
            if calories is None:
                continue

            carbs, protein, fat, fiber = _extract_macros_per_100g(food_dict)

            normalized.append(
                FoodNormalized(
                    name=description,
                    brand=str(food_dict.get("brandOwner", "")).strip() or None,
                    calories_per_100g=round(calories, 2),
                    protein_per_100g=round(protein, 2),
                    fat_per_100g=round(fat, 2),
                    carbs_per_100g=round(carbs, 2),
                    fiber_per_100g=round(fiber, 2) if fiber is not None else None,
                    source=self.source_name,
                    confidence_score=clamp_confidence(USDA_BASE_CONFIDENCE),
                )
            )

        return normalized


def _extract_kcal_per_100g(food: dict[str, Any]) -> float | None:
    nutrients = food.get("foodNutrients", [])
    if not isinstance(nutrients, list):
        return None

    nutrients_list = cast(list[Any], nutrients)
    for nutrient in nutrients_list:
        if not isinstance(nutrient, dict):
            continue
        nutrient_dict = cast(dict[str, Any], nutrient)

        nutrient_name = str(nutrient_dict.get("nutrientName", "")).lower()
        unit_name = str(nutrient_dict.get("unitName", "")).upper()
        value = nutrient_dict.get("value")

        if "energy" in nutrient_name and unit_name == "KCAL":
            try:
                if value is None:
                    return None
                return float(value)
            except (TypeError, ValueError):
                return None

    return None


def _extract_macros_per_100g(food: dict[str, Any]) -> tuple[float, float, float, float | None]:
    nutrients = food.get("foodNutrients", [])
    if not isinstance(nutrients, list):
        return (0.0, 0.0, 0.0, None)

    carbs = 0.0
    protein = 0.0
    fat = 0.0
    fiber: float | None = None

    nutrients_list = cast(list[Any], nutrients)
    for nutrient in nutrients_list:
        if not isinstance(nutrient, dict):
            continue
        nutrient_dict = cast(dict[str, Any], nutrient)

        nutrient_name = str(nutrient_dict.get("nutrientName", "")).lower()
        nutrient_number = str(nutrient_dict.get("nutrientNumber", "")).strip()
        unit_name = str(nutrient_dict.get("unitName", "")).upper()

        if unit_name != "G":
            continue

        try:
            value_raw = nutrient_dict.get("value")
            if value_raw is None:
                continue
            value = float(value_raw)
        except (TypeError, ValueError):
            continue

        if nutrient_number == "1005" or "carbohydrate" in nutrient_name:
            carbs = value
        elif nutrient_number == "1003" or "protein" in nutrient_name:
            protein = value
        elif nutrient_number == "1004" or "total lipid" in nutrient_name or nutrient_name == "fat":
            fat = value
        elif nutrient_number == "1079" or "fiber" in nutrient_name:
            fiber = value

    return (carbs, protein, fat, fiber)
