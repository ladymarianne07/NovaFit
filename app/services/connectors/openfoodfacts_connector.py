from __future__ import annotations

import logging
from typing import Any, cast

import httpx

from ...config import settings
from ...schemas.food_normalized import FoodNormalized
from .base_connector import FoodConnector, clamp_confidence, first_non_empty


logger = logging.getLogger(__name__)

OPENFOODFACTS_BASE_CONFIDENCE = 0.85
OPENFOODFACTS_SEARCH_URL = "https://world.openfoodfacts.org/cgi/search.pl"
OPENFOODFACTS_TIMEOUT_SECONDS = 8.0


class OpenFoodFactsConnector(FoodConnector):
    """Connector for Open Food Facts search endpoint."""

    source_name = "openfoodfacts"

    def __init__(self, timeout_seconds: float = OPENFOODFACTS_TIMEOUT_SECONDS) -> None:
        self.timeout_seconds = timeout_seconds

    async def search(self, query: str) -> list[FoodNormalized]:
        params: dict[str, str] = {
            "search_terms": query,
            "search_simple": "1",
            "action": "process",
            "json": "1",
            "page_size": "15",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(
                    OPENFOODFACTS_SEARCH_URL,
                    params=params,
                    headers={"User-Agent": settings.OPENFOODFACTS_USER_AGENT},
                )
                response.raise_for_status()
        except httpx.TimeoutException:
            logger.warning("OpenFoodFacts connector timeout for query='%s'", query)
            return []
        except httpx.HTTPError as exc:
            logger.warning("OpenFoodFacts connector request failed for query='%s': %s", query, exc)
            return []

        data_raw: Any = response.json()
        if not isinstance(data_raw, dict):
            return []

        data = cast(dict[str, Any], data_raw)
        products_raw = data.get("products", [])
        if not isinstance(products_raw, list):
            return []

        products = cast(list[Any], products_raw)

        normalized: list[FoodNormalized] = []
        for product in products:
            if not isinstance(product, dict):
                continue

            product_dict = cast(dict[str, Any], product)

            nutriments_raw = product_dict.get("nutriments", {})
            if not isinstance(nutriments_raw, dict):
                continue
            nutriments = cast(dict[str, Any], nutriments_raw)

            name = first_non_empty(
                [
                    product_dict.get("product_name_en"),
                    product_dict.get("product_name"),
                    product_dict.get("generic_name_en"),
                    product_dict.get("generic_name"),
                ]
            )
            if not name:
                continue

            calories = _to_float(nutriments.get("energy-kcal_100g"))
            if calories is None:
                # Fallback from kJ -> kcal when needed.
                energy_kj = _to_float(nutriments.get("energy-kj_100g"))
                calories = round((energy_kj / 4.184), 2) if energy_kj is not None else None

            if calories is None:
                continue

            protein = _to_float(nutriments.get("proteins_100g"), default=0.0) or 0.0
            fat = _to_float(nutriments.get("fat_100g"), default=0.0) or 0.0
            carbs = _to_float(nutriments.get("carbohydrates_100g"), default=0.0) or 0.0
            fiber = _to_float(nutriments.get("fiber_100g"))

            brand = first_non_empty([product_dict.get("brands"), product_dict.get("brand_owner")])
            has_barcode = bool(str(product_dict.get("code", "")).strip())

            base_confidence = OPENFOODFACTS_BASE_CONFIDENCE + (0.03 if has_barcode else -0.03)

            normalized.append(
                FoodNormalized(
                    name=name,
                    brand=brand,
                    calories_per_100g=round(calories, 2),
                    protein_per_100g=round(protein, 2),
                    fat_per_100g=round(fat, 2),
                    carbs_per_100g=round(carbs, 2),
                    fiber_per_100g=round(fiber, 2) if fiber is not None else None,
                    source=self.source_name,
                    confidence_score=clamp_confidence(base_confidence),
                )
            )

        return normalized


def _to_float(value: Any, default: float | None = None) -> float | None:
    if value is None:
        return default

    try:
        return float(value)
    except (TypeError, ValueError):
        return default
