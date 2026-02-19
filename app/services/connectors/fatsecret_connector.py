from __future__ import annotations

import logging
from typing import Any

import httpx

from ...config import settings
from ...schemas.food_normalized import FoodNormalized
from .base_connector import FoodConnector, clamp_confidence, first_non_empty


logger = logging.getLogger(__name__)

FATSECRET_BASE_CONFIDENCE = 0.8
FATSECRET_TIMEOUT_SECONDS = 8.0
FATSECRET_OAUTH_URL = "https://oauth.fatsecret.com/connect/token"
FATSECRET_API_URL = "https://platform.fatsecret.com/rest/server.api"


class FatSecretConnector(FoodConnector):
    """Connector for FatSecret Platform API (OAuth2 Client Credentials)."""

    source_name = "fatsecret"

    def __init__(self, timeout_seconds: float = FATSECRET_TIMEOUT_SECONDS) -> None:
        self.timeout_seconds = timeout_seconds

    async def search(self, query: str) -> list[FoodNormalized]:
        if not settings.FATSECRET_CLIENT_ID or not settings.FATSECRET_CLIENT_SECRET:
            logger.info("FatSecret credentials not configured; skipping connector")
            return []

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                access_token = await self._get_access_token(client)
                if not access_token:
                    return []

                response = await client.get(
                    FATSECRET_API_URL,
                    params={
                        "method": "foods.search.v3",
                        "search_expression": query,
                        "format": "json",
                    },
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                response.raise_for_status()
        except httpx.TimeoutException:
            logger.warning("FatSecret connector timeout for query='%s'", query)
            return []
        except httpx.HTTPError as exc:
            logger.warning("FatSecret connector request failed for query='%s': %s", query, exc)
            return []

        data = response.json()
        foods_node = data.get("foods", {}) if isinstance(data, dict) else {}
        food_list = foods_node.get("food", []) if isinstance(foods_node, dict) else []

        if isinstance(food_list, dict):
            food_list = [food_list]

        if not isinstance(food_list, list):
            return []

        normalized: list[FoodNormalized] = []
        for item in food_list:
            if not isinstance(item, dict):
                continue

            name = first_non_empty([item.get("food_name")])
            if not name:
                continue

            calories, protein, fat, carbs, fiber = _extract_per_100g_from_description(
                str(item.get("food_description", ""))
            )

            if calories is None:
                # FatSecret search payload may not provide per-100g reliably.
                # We skip non-normalizable items to keep output strict.
                continue

            normalized.append(
                FoodNormalized(
                    name=name,
                    brand=first_non_empty([item.get("brand_name")]),
                    calories_per_100g=round(calories, 2),
                    protein_per_100g=round(protein or 0.0, 2),
                    fat_per_100g=round(fat or 0.0, 2),
                    carbs_per_100g=round(carbs or 0.0, 2),
                    fiber_per_100g=round(fiber, 2) if fiber is not None else None,
                    source=self.source_name,
                    confidence_score=clamp_confidence(FATSECRET_BASE_CONFIDENCE),
                )
            )

        return normalized

    async def _get_access_token(self, client: httpx.AsyncClient) -> str | None:
        try:
            response = await client.post(
                FATSECRET_OAUTH_URL,
                auth=(settings.FATSECRET_CLIENT_ID, settings.FATSECRET_CLIENT_SECRET),
                data={"grant_type": "client_credentials", "scope": "basic"},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("FatSecret OAuth failed: %s", exc)
            return None

        data = response.json()
        token = data.get("access_token") if isinstance(data, dict) else None
        return str(token).strip() if token else None


def _extract_per_100g_from_description(
    description: str,
) -> tuple[float | None, float | None, float | None, float | None, float | None]:
    """
    Parse FatSecret free-text description trying to extract values tagged as per 100g.

    Example formats vary. If per-100g cannot be reliably inferred, returns calories=None.
    """
    text = description.lower()
    if "per 100g" not in text and "100g" not in text:
        return (None, None, None, None, None)

    import re

    def _find(pattern: str) -> float | None:
        match = re.search(pattern, text)
        if not match:
            return None
        try:
            return float(match.group(1))
        except (TypeError, ValueError):
            return None

    calories = _find(r"calories:\s*([0-9]+(?:\.[0-9]+)?)")
    fat = _find(r"fat:\s*([0-9]+(?:\.[0-9]+)?)g")
    carbs = _find(r"carbs?:\s*([0-9]+(?:\.[0-9]+)?)g")
    protein = _find(r"protein:\s*([0-9]+(?:\.[0-9]+)?)g")
    fiber = _find(r"fiber:\s*([0-9]+(?:\.[0-9]+)?)g")

    return (calories, protein, fat, carbs, fiber)
