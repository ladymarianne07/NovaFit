from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from rapidfuzz import fuzz

from ..config import settings


logger = logging.getLogger(__name__)

FATSECRET_OAUTH_URL = "https://oauth.fatsecret.com/connect/token"
FATSECRET_API_URL = "https://platform.fatsecret.com/rest/server.api"
FATSECRET_TIMEOUT_SECONDS = 8.0
FATSECRET_TOKEN_TTL_SECONDS = 60 * 45
FATSECRET_MIN_SIMILARITY_THRESHOLD = 55.0
FATSECRET_SEARCH_LIMIT = 10
OZ_TO_GRAMS = 28.3495

_FATSECRET_HTTP_CLIENT = httpx.Client(timeout=FATSECRET_TIMEOUT_SECONDS)
_FATSECRET_ACCESS_TOKENS: dict[str, tuple[str, datetime]] = {}


class FatSecretServiceError(Exception):
    """Raised when FatSecret search fails or returns unusable data."""


@dataclass
class FatSecretFoodResult:
    """Normalized FatSecret match used by application service layer."""

    food_id: str
    description: str
    calories_per_100g: float
    carbs_per_100g: float
    protein_per_100g: float
    fat_per_100g: float
    serving_size_grams: float | None = None


@dataclass
class FatSecretNLPItem:
    """Normalized item returned by FatSecret NLP endpoint."""

    food_id: str
    food_name: str
    quantity_grams: float
    total_calories: float
    total_carbs: float
    total_protein: float
    total_fat: float


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _extract_per_100g_from_description(
    description: str,
) -> tuple[float | None, float | None, float | None, float | None]:
    """Parse FatSecret free-text description and return kcal/carb/protein/fat per 100g."""
    text = description.lower()
    if "100g" not in text and "per 100" not in text:
        return (None, None, None, None)

    def _find(pattern: str) -> float | None:
        match = re.search(pattern, text)
        if not match:
            return None
        return _safe_float(match.group(1))

    calories = _find(r"calories:\s*([0-9]+(?:\.[0-9]+)?)")
    carbs = _find(r"carbs?:\s*([0-9]+(?:\.[0-9]+)?)g")
    protein = _find(r"protein:\s*([0-9]+(?:\.[0-9]+)?)g")
    fat = _find(r"fat:\s*([0-9]+(?:\.[0-9]+)?)g")

    return (calories, carbs, protein, fat)


def _extract_servings(food_payload: dict[str, Any]) -> list[dict[str, Any]]:
    servings_node = food_payload.get("servings", {}) if isinstance(food_payload, dict) else {}
    servings = servings_node.get("serving", []) if isinstance(servings_node, dict) else []

    if isinstance(servings, dict):
        servings = [servings]

    if not isinstance(servings, list):
        return []

    return [entry for entry in servings if isinstance(entry, dict)]


def _metric_amount_in_grams(metric_amount: float | None, metric_unit: str) -> float | None:
    if metric_amount is None or metric_amount <= 0:
        return None

    unit = metric_unit.strip().lower()
    if unit in {"g", "gram", "grams"}:
        return metric_amount
    if unit in {"ml", "milliliter", "milliliters"}:
        # For most beverages this is a practical approximation used by many nutrition systems.
        return metric_amount
    if unit in {"oz", "ounce", "ounces"}:
        return metric_amount * OZ_TO_GRAMS

    return None


def _to_serving_macros(serving: dict[str, Any]) -> tuple[float | None, float | None, float | None, float | None]:
    calories = _safe_float(serving.get("calories"))
    carbs = _safe_float(serving.get("carbohydrate"))
    protein = _safe_float(serving.get("protein"))
    fat = _safe_float(serving.get("fat"))
    return (calories, carbs, protein, fat)


def _pick_per_100_serving(servings: list[dict[str, Any]]) -> dict[str, Any] | None:
    # v5 may include derived standardized serving_id=0 (e.g., 100 g / 100 ml)
    for serving in servings:
        serving_id = str(serving.get("serving_id", "")).strip()
        if serving_id == "0":
            return serving

    for serving in servings:
        description = str(serving.get("serving_description", "")).strip().lower()
        if description.startswith("100 g") or description.startswith("100 ml"):
            return serving

    for serving in servings:
        metric_amount = _safe_float(serving.get("metric_serving_amount"))
        metric_unit = str(serving.get("metric_serving_unit", "")).strip().lower()
        normalized_amount = _metric_amount_in_grams(metric_amount, metric_unit)
        if normalized_amount is not None and abs(normalized_amount - 100.0) <= 1.0:
            return serving

    return None


def _derive_per_100_from_serving(serving: dict[str, Any]) -> tuple[float, float, float, float] | None:
    calories, carbs, protein, fat = _to_serving_macros(serving)
    if calories is None:
        return None

    metric_amount = _safe_float(serving.get("metric_serving_amount"))
    metric_unit = str(serving.get("metric_serving_unit", "")).strip().lower()
    grams_amount = _metric_amount_in_grams(metric_amount, metric_unit)
    if grams_amount is None or grams_amount <= 0:
        return None

    factor = 100.0 / grams_amount
    return (
        round(calories * factor, 2),
        round((carbs or 0.0) * factor, 2),
        round((protein or 0.0) * factor, 2),
        round((fat or 0.0) * factor, 2),
    )


def _pick_default_serving_grams(servings: list[dict[str, Any]]) -> float | None:
    default_candidates = [
        serving
        for serving in servings
        if str(serving.get("is_default", "")).strip() in {"1", "true", "True"}
    ]

    search_space = default_candidates or servings
    for serving in search_space:
        metric_amount = _safe_float(serving.get("metric_serving_amount"))
        metric_unit = str(serving.get("metric_serving_unit", "")).strip().lower()
        grams_amount = _metric_amount_in_grams(metric_amount, metric_unit)
        if grams_amount is not None and grams_amount > 0:
            return round(grams_amount, 2)

    return None


def _extract_best_per_100_from_food_payload(food_payload: dict[str, Any]) -> tuple[float, float, float, float, float | None] | None:
    servings = _extract_servings(food_payload)
    if not servings:
        return None

    default_serving_grams = _pick_default_serving_grams(servings)

    per_100_serving = _pick_per_100_serving(servings)
    if per_100_serving is not None:
        calories, carbs, protein, fat = _to_serving_macros(per_100_serving)
        if calories is not None:
            return (
                round(calories, 2),
                round(carbs or 0.0, 2),
                round(protein or 0.0, 2),
                round(fat or 0.0, 2),
                default_serving_grams,
            )

    # If no explicit 100g/100ml serving exists, derive from first valid metric serving.
    for serving in servings:
        derived = _derive_per_100_from_serving(serving)
        if derived is None:
            continue
        calories_100, carbs_100, protein_100, fat_100 = derived
        return (calories_100, carbs_100, protein_100, fat_100, default_serving_grams)

    return None


def _get_food_details_v5(access_token: str, food_id: str) -> dict[str, Any] | None:
    try:
        response = _FATSECRET_HTTP_CLIENT.get(
            FATSECRET_API_URL,
            params={
                "method": "food.get.v5",
                "food_id": food_id,
                "format": "json",
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
    except httpx.HTTPError:
        return None

    payload = response.json()
    food_node = payload.get("food", {}) if isinstance(payload, dict) else {}
    return food_node if isinstance(food_node, dict) else None


def _get_access_token(scope: str = "basic") -> str:
    if not settings.FATSECRET_CLIENT_ID or not settings.FATSECRET_CLIENT_SECRET:
        raise FatSecretServiceError("missing_fatsecret_credentials")

    now = datetime.now(timezone.utc)
    cached = _FATSECRET_ACCESS_TOKENS.get(scope)
    if cached is not None:
        cached_token, cached_expires_at = cached
        if now < cached_expires_at:
            return cached_token

    try:
        response = _FATSECRET_HTTP_CLIENT.post(
            FATSECRET_OAUTH_URL,
            auth=(settings.FATSECRET_CLIENT_ID, settings.FATSECRET_CLIENT_SECRET),
            data={"grant_type": "client_credentials", "scope": scope},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise FatSecretServiceError("fatsecret_oauth_failed") from exc

    payload = response.json()
    if not isinstance(payload, dict):
        raise FatSecretServiceError("fatsecret_oauth_failed")

    token = payload.get("access_token")
    if token is None:
        raise FatSecretServiceError("fatsecret_oauth_failed")

    token_text = str(token).strip()
    if not token_text:
        raise FatSecretServiceError("fatsecret_oauth_failed")

    _FATSECRET_ACCESS_TOKENS[scope] = (
        token_text,
        now + timedelta(seconds=FATSECRET_TOKEN_TTL_SECONDS),
    )
    return token_text


def search_food_by_name(normalized_name: str) -> FatSecretFoodResult:
    """Search FatSecret and return best ranked per-100g normalized result."""
    access_token = _get_access_token()

    try:
        response = _FATSECRET_HTTP_CLIENT.get(
            FATSECRET_API_URL,
            params={
                "method": "foods.search.v3",
                "search_expression": normalized_name,
                "max_results": FATSECRET_SEARCH_LIMIT,
                "format": "json",
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise FatSecretServiceError("fatsecret_request_failed") from exc

    payload = response.json()
    foods_node = payload.get("foods", {}) if isinstance(payload, dict) else {}
    foods = foods_node.get("food", []) if isinstance(foods_node, dict) else []

    if isinstance(foods, dict):
        foods = [foods]

    if not isinstance(foods, list) or not foods:
        raise FatSecretServiceError("food_not_found")

    typed_foods = [item for item in foods if isinstance(item, dict)]
    typed_foods.sort(
        key=lambda item: fuzz.partial_token_set_ratio(normalized_name, str(item.get("food_name", ""))),
        reverse=True,
    )

    for item in typed_foods[:FATSECRET_SEARCH_LIMIT]:
        food_name = str(item.get("food_name", "")).strip()
        if not food_name:
            continue

        similarity = float(fuzz.partial_token_set_ratio(normalized_name, food_name))
        if similarity < FATSECRET_MIN_SIMILARITY_THRESHOLD:
            continue

        food_id = str(item.get("food_id", "")).strip()
        if not food_id:
            continue

        # Preferred path: use detailed serving payload for precise macros and measures.
        detail_payload = _get_food_details_v5(access_token=access_token, food_id=food_id)
        if detail_payload is not None:
            extracted = _extract_best_per_100_from_food_payload(detail_payload)
            if extracted is not None:
                calories, carbs, protein, fat, serving_size_grams = extracted
                return FatSecretFoodResult(
                    food_id=food_id,
                    description=food_name,
                    calories_per_100g=calories,
                    carbs_per_100g=carbs,
                    protein_per_100g=protein,
                    fat_per_100g=fat,
                    serving_size_grams=serving_size_grams,
                )

        # Fallback path: parse summary description if detail payload is unusable.
        description_text = str(item.get("food_description", ""))
        calories, carbs, protein, fat = _extract_per_100g_from_description(description_text)
        if calories is None:
            continue

        return FatSecretFoodResult(
            food_id=food_id,
            description=food_name,
            calories_per_100g=round(calories, 2),
            carbs_per_100g=round(carbs or 0.0, 2),
            protein_per_100g=round(protein or 0.0, 2),
            fat_per_100g=round(fat or 0.0, 2),
            serving_size_grams=None,
        )

    raise FatSecretServiceError("food_not_found")


def parse_natural_language_foods(user_input: str) -> list[FatSecretNLPItem]:
    """Parse free text using FatSecret NLP and return normalized food items."""
    text = user_input.strip()
    if not text:
        raise FatSecretServiceError("insufficient_data")

    access_token = _get_access_token(scope="basic nlp")

    try:
        response = _FATSECRET_HTTP_CLIENT.post(
            "https://platform.fatsecret.com/rest/natural-language-processing/v1",
            json={
                "user_input": text,
                "include_food_data": False,
            },
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise FatSecretServiceError("fatsecret_nlp_request_failed") from exc

    payload = response.json()
    food_response = payload.get("food_response", []) if isinstance(payload, dict) else []
    if not isinstance(food_response, list) or not food_response:
        raise FatSecretServiceError("food_not_found")

    normalized_items: list[FatSecretNLPItem] = []
    for item in food_response:
        if not isinstance(item, dict):
            continue

        food_id = str(item.get("food_id", "")).strip()
        if not food_id:
            continue

        food_name = str(item.get("food_entry_name", "")).strip()
        if not food_name:
            food_name = "unknown"

        eaten = item.get("eaten")
        if not isinstance(eaten, dict):
            continue

        total_metric_amount = _safe_float(eaten.get("total_metric_amount"))
        if total_metric_amount is None or total_metric_amount <= 0:
            per_unit_metric_amount = _safe_float(eaten.get("per_unit_metric_amount"))
            units = _safe_float(eaten.get("units"))
            if per_unit_metric_amount is None or units is None:
                continue
            total_metric_amount = per_unit_metric_amount * units

        nutrition = eaten.get("total_nutritional_content")
        if not isinstance(nutrition, dict):
            continue

        calories = _safe_float(nutrition.get("calories"))
        carbs = _safe_float(nutrition.get("carbohydrate"))
        protein = _safe_float(nutrition.get("protein"))
        fat = _safe_float(nutrition.get("fat"))

        if calories is None:
            continue

        normalized_items.append(
            FatSecretNLPItem(
                food_id=food_id,
                food_name=food_name,
                quantity_grams=round(total_metric_amount, 2),
                total_calories=round(calories, 2),
                total_carbs=round(carbs or 0.0, 2),
                total_protein=round(protein or 0.0, 2),
                total_fat=round(fat or 0.0, 2),
            )
        )

    if not normalized_items:
        raise FatSecretServiceError("food_not_found")

    return normalized_items
