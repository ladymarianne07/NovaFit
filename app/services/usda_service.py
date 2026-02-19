import logging
from dataclasses import dataclass
from typing import Any, cast

import httpx
from rapidfuzz import fuzz

from ..config import settings


USDA_SEARCH_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"
# Keep a conservative floor but allow common generic queries (e.g., "fish")
# that can score in the high 50s depending on USDA description phrasing.
MIN_SIMILARITY_THRESHOLD = 55.0


logger = logging.getLogger(__name__)


class USDAServiceError(Exception):
    """Raised when USDA search fails or returns unusable data."""


@dataclass
class USDAFoodResult:
    """Normalized USDA match used by application service layer."""

    fdc_id: str
    description: str
    calories_per_100g: float
    carbs_per_100g: float
    protein_per_100g: float
    fat_per_100g: float
    serving_size_grams: float | None = None


@dataclass
class RankedUSDAResult:
    """Internal ranking structure for USDA candidates."""

    food: dict[str, Any]
    description: str
    category: str
    similarity_score: float
    weighted_score: float


def _extract_calories_per_100g(food: dict[str, Any]) -> float | None:
    nutrients: Any = food.get("foodNutrients", [])
    if not isinstance(nutrients, list):
        return None

    nutrients_list = cast(list[Any], nutrients)
    for nutrient in nutrients_list:
        if not isinstance(nutrient, dict):
            continue

        nutrient_dict = cast(dict[str, Any], nutrient)
        nutrient_name = str(nutrient_dict.get("nutrientName", "")).lower()
        unit_name = str(nutrient_dict.get("unitName", "")).upper()
        value: Any = nutrient_dict.get("value")

        if "energy" in nutrient_name and unit_name == "KCAL":
            try:
                return float(value)
            except (TypeError, ValueError):
                return None
    return None


def _extract_macros_per_100g(food: dict[str, Any]) -> tuple[float, float, float]:
    """Extract carbs, protein, and fat values per 100g from USDA payload."""
    nutrients: Any = food.get("foodNutrients", [])
    if not isinstance(nutrients, list):
        return (0.0, 0.0, 0.0)

    carbs = 0.0
    protein = 0.0
    fat = 0.0

    nutrients_list = cast(list[Any], nutrients)
    for nutrient in nutrients_list:
        if not isinstance(nutrient, dict):
            continue

        nutrient_dict = cast(dict[str, Any], nutrient)
        nutrient_name = str(nutrient_dict.get("nutrientName", "")).lower()
        nutrient_number = str(nutrient_dict.get("nutrientNumber", "")).strip()
        unit_name = str(nutrient_dict.get("unitName", "")).upper()
        value: Any = nutrient_dict.get("value")

        if unit_name != "G":
            continue

        try:
            nutrient_value = float(value)
        except (TypeError, ValueError):
            continue

        # USDA nutrient numbers: 1005 carbs, 1003 protein, 1004 fat
        if nutrient_number == "1005" or "carbohydrate" in nutrient_name:
            carbs = nutrient_value
        elif nutrient_number == "1003" or "protein" == nutrient_name or "protein" in nutrient_name:
            protein = nutrient_value
        elif nutrient_number == "1004" or "total lipid" in nutrient_name or "fat" == nutrient_name:
            fat = nutrient_value

    return (round(carbs, 2), round(protein, 2), round(fat, 2))


def _extract_serving_size_grams(food: dict[str, Any]) -> float | None:
    """Extract serving size in grams when available from USDA payload."""
    serving_size_raw: Any = food.get("servingSize")
    serving_unit = str(food.get("servingSizeUnit", "")).strip().lower()

    if serving_size_raw is None:
        return None

    try:
        serving_size_value = float(serving_size_raw)
    except (TypeError, ValueError):
        return None

    if serving_size_value <= 0:
        return None

    if serving_unit in {"g", "gram", "grams", "gm"}:
        return round(serving_size_value, 2)

    # USDA household serving often lacks explicit gram conversion.
    return None


def _extract_food_category(food: dict[str, Any]) -> str:
    """Extract USDA category label from dataType/foodCategory fields."""
    data_type = str(food.get("dataType", "")).strip()
    if data_type:
        return data_type

    food_category = food.get("foodCategory")
    if isinstance(food_category, dict):
        category_dict = cast(dict[str, Any], food_category)
        return str(category_dict.get("description", "")).strip()

    return str(food_category or "Unknown").strip() or "Unknown"


def _category_priority_bonus(category: str) -> float:
    """Return category weighting bonus to prioritize high-quality USDA entries."""
    lowered = category.lower()

    if "foundation" in lowered:
        return 12.0
    if "sr legacy" in lowered:
        return 10.0
    if "survey" in lowered or "fndds" in lowered:
        return 6.0
    if "branded" in lowered:
        return -6.0

    return 0.0


def _compute_similarity_score(normalized_name: str, description: str) -> float:
    """Compute robust similarity score using token_sort_ratio (0-100)."""
    return float(
        fuzz.token_sort_ratio(
            normalized_name.lower().strip(),
            description.lower().strip(),
        )
    )


def rank_usda_results(normalized_name: str, foods: list[dict[str, Any]]) -> list[RankedUSDAResult]:
    """Rank USDA candidates by weighted score = similarity + category priority."""
    ranked: list[RankedUSDAResult] = []

    for food in foods[:5]:
        description = str(food.get("description", "")).strip()
        if not description:
            continue

        category = _extract_food_category(food)
        similarity = _compute_similarity_score(normalized_name, description)
        weighted = similarity + _category_priority_bonus(category)

        ranked.append(
            RankedUSDAResult(
                food=food,
                description=description,
                category=category,
                similarity_score=similarity,
                weighted_score=weighted,
            )
        )

    ranked.sort(key=lambda item: item.weighted_score, reverse=True)

    for candidate in ranked:
        logger.info(
            "USDA candidate | query='%s' | desc='%s' | category='%s' | sim=%.2f | weighted=%.2f",
            normalized_name,
            candidate.description,
            candidate.category,
            candidate.similarity_score,
            candidate.weighted_score,
        )

    return ranked


def _search_usda_top_results(normalized_name: str) -> list[dict[str, Any]]:
    """Call USDA API and return top 5 candidate foods."""
    if not settings.USDA_API_KEY:
        raise USDAServiceError("missing_usda_api_key")

    payload: dict[str, Any] = {
        "query": normalized_name,
        "pageSize": 5,
    }

    try:
        response = httpx.post(
            USDA_SEARCH_URL,
            params={"api_key": settings.USDA_API_KEY},
            json=payload,
            timeout=15.0,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise USDAServiceError("usda_request_failed") from exc

    data: dict[str, Any] = response.json()
    foods: Any = data.get("foods", [])

    if not isinstance(foods, list) or not foods:
        raise USDAServiceError("food_not_found")

    foods_list = cast(list[Any], foods)
    typed_foods: list[dict[str, Any]] = []
    for food_item in foods_list[:5]:
        if isinstance(food_item, dict):
            typed_foods.append(cast(dict[str, Any], food_item))

    return typed_foods


def _select_best_candidate(normalized_name: str, ranked_results: list[RankedUSDAResult]) -> RankedUSDAResult:
    """Select best USDA candidate with similarity threshold guard."""
    if not ranked_results:
        raise USDAServiceError("food_not_found")

    best = ranked_results[0]
    if best.similarity_score < MIN_SIMILARITY_THRESHOLD:
        logger.warning(
            "USDA low similarity match | query='%s' | best_desc='%s' | sim=%.2f",
            normalized_name,
            best.description,
            best.similarity_score,
        )
        raise USDAServiceError("low_similarity_match")

    return best


def _build_food_result_from_candidate(candidate: RankedUSDAResult) -> USDAFoodResult:
    """Extract required USDA fields from selected candidate."""
    calories = _extract_calories_per_100g(candidate.food)
    if calories is None:
        raise USDAServiceError("no_calorie_data")

    fdc_id = str(candidate.food.get("fdcId", "")).strip()
    description = candidate.description
    if not fdc_id or not description:
        raise USDAServiceError("food_not_found")

    serving_size_grams = _extract_serving_size_grams(candidate.food)
    carbs_per_100g, protein_per_100g, fat_per_100g = _extract_macros_per_100g(candidate.food)

    return USDAFoodResult(
        fdc_id=fdc_id,
        description=description,
        calories_per_100g=round(calories, 2),
        carbs_per_100g=carbs_per_100g,
        protein_per_100g=protein_per_100g,
        fat_per_100g=fat_per_100g,
        serving_size_grams=serving_size_grams,
    )


def search_food_by_name(normalized_name: str) -> USDAFoodResult:
    """Search USDA FoodData Central and return best ranked result."""
    foods = _search_usda_top_results(normalized_name)
    ranked_results = rank_usda_results(normalized_name, foods)
    best_candidate = _select_best_candidate(normalized_name, ranked_results)
    return _build_food_result_from_candidate(best_candidate)
