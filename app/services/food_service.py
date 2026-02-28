from sqlalchemy.orm import Session
from datetime import datetime, timezone
from uuid import uuid4
from time import perf_counter
import logging
import re

from ..models.food import FoodEntry
from ..schemas.food import (
    FoodItemDistributionResponse,
    FoodParseCalculateResponse,
    FoodParseLogResponse,
    ParsedFoodPayload,
    ParsedMealResponse,
)
from ..schemas.nutrition import MealLogCreate
from .food_parser import (
    FoodParserError,
    convert_to_grams,
    is_serving_unit,
    meal_label_for_type,
    parse_food_input,
    split_text_by_meal_type,
)
from .nutrition_service import NutritionService
from .portion_resolver_service import PortionResolverService
from .fatsecret_service import (
    FatSecretServiceError,
    search_food_by_name as search_fatsecret_food_by_name,
)
from .usda_service import USDAServiceError, search_food_by_name


class FoodServiceError(Exception):
    """Base exception for food service workflow errors."""


logger = logging.getLogger(__name__)


class FoodService:
    """Service layer for food parsing, multi-source lookup, caching, and nutrition calculation."""

    SCRAMBLED_EGG_TOKENS = {
        "scrambled egg",
        "scrambled eggs",
        "huevo revuelto",
        "huevos revueltos",
    }
    BUTTER_TOKENS = {"butter", "manteca", "margarine", "ghee"}
    TOAST_TOKENS = {"toast", "tostada", "whole wheat toast", "pan tostado"}
    MILK_TOKENS = {"milk", "leche"}
    COFFEE_TOKENS = {"coffee", "cafe", "café"}
    SWEETENER_TOKENS = {"sweetener", "edulcorante"}

    DEFAULT_SERVING_GRAMS = 100.0
    PORTION_UNITS = {
        "serving",
        "portion",
        "porción",
        "porcion",
        "cup",
        "cups",
        "taza",
        "tazas",
        "tablespoon",
        "tablespoons",
        "tbsp",
        "cucharada",
        "cucharadas",
        "teaspoon",
        "teaspoons",
        "tsp",
        "cucharadita",
        "cucharaditas",
        "piece",
        "pieza",
        "unidad",
        "unit",
        "ml",
    }
    FAST_LOCAL_CONVERSION_UNITS = {
        "g",
        "gram",
        "grams",
        "gramo",
        "gramos",
        "kg",
        "kilogram",
        "kilograms",
        "kilogramo",
        "kilogramos",
        "oz",
        "onza",
        "onzas",
        "lb",
        "lbs",
        "libra",
        "libras",
        "cup",
        "cups",
        "taza",
        "tazas",
        "tablespoon",
        "tablespoons",
        "tbsp",
        "cucharada",
        "cucharadas",
        "teaspoon",
        "teaspoons",
        "tsp",
        "cucharadita",
        "cucharaditas",
        "ml",
    }

    @staticmethod
    def _to_per_100g(total_value: float, quantity_grams: float) -> float:
        if quantity_grams <= 0:
            return 0.0
        return round((total_value / quantity_grams) * 100.0, 2)

    @classmethod
    def _persist_aggregate_calculation(
        cls,
        db: Session,
        original_text: str,
        normalized_names: list[str],
        source_ids: list[str],
        aggregate_quantity_grams: float,
        aggregate_total_calories: float,
        aggregate_total_carbs: float,
        aggregate_total_protein: float,
        aggregate_total_fat: float,
    ) -> FoodParseCalculateResponse:
        if aggregate_quantity_grams <= 0:
            raise FoodServiceError("insufficient_data")

        calories_per_100g = cls._to_per_100g(aggregate_total_calories, aggregate_quantity_grams)
        carbs_per_100g = cls._to_per_100g(aggregate_total_carbs, aggregate_quantity_grams)
        protein_per_100g = cls._to_per_100g(aggregate_total_protein, aggregate_quantity_grams)
        fat_per_100g = cls._to_per_100g(aggregate_total_fat, aggregate_quantity_grams)

        normalized_name = " + ".join(dict.fromkeys(normalized_names))
        source_id = source_ids[0] if len(source_ids) == 1 else "multi"

        quantity_grams = round(aggregate_quantity_grams, 2)
        total_calories = round(aggregate_total_calories, 2)
        total_carbs = round(aggregate_total_carbs, 2)
        total_protein = round(aggregate_total_protein, 2)
        total_fat = round(aggregate_total_fat, 2)

        food_entry = FoodEntry(
            original_text=original_text.strip(),
            normalized_name=normalized_name,
            quantity_grams=quantity_grams,
            usda_fdc_id=source_id,
            calories_per_100g=calories_per_100g,
            total_calories=total_calories,
        )
        db.add(food_entry)
        db.commit()

        return FoodParseCalculateResponse(
            food=normalized_name,
            quantity_grams=quantity_grams,
            calories_per_100g=round(calories_per_100g, 2),
            carbs_per_100g=round(carbs_per_100g, 2),
            protein_per_100g=round(protein_per_100g, 2),
            fat_per_100g=round(fat_per_100g, 2),
            total_calories=total_calories,
            total_carbs=total_carbs,
            total_protein=total_protein,
            total_fat=total_fat,
        )

    @staticmethod
    def _has_explicit_quantity(text: str) -> bool:
        return bool(re.search(r"\d", text or ""))

    @classmethod
    def _contains_any_token(cls, text: str, tokens: set[str]) -> bool:
        lowered = text.strip().lower()
        return any(token in lowered for token in tokens)

    @classmethod
    def _normalize_ambiguous_items(
        cls,
        parsed_items: list[ParsedFoodPayload],
        original_text: str,
    ) -> list[ParsedFoodPayload]:
        has_explicit_quantity_in_text = cls._has_explicit_quantity(original_text)

        has_explicit_butter = any(cls._contains_any_token(item.name, cls.BUTTER_TOKENS) for item in parsed_items)

        normalized: list[ParsedFoodPayload] = []
        for item in parsed_items:
            lowered_name = item.name.strip().lower()
            lowered_unit = item.unit.strip().lower()

            if cls._contains_any_token(lowered_name, cls.SCRAMBLED_EGG_TOKENS):
                # Avoid treating "scrambled eggs" as a heavy prepared serving from databases.
                # Map to plain egg units to prevent hidden fats and oversized serving defaults.
                egg_pieces = item.quantity if item.quantity > 1 else 2.0
                normalized.append(ParsedFoodPayload(name="egg", quantity=egg_pieces, unit="piece"))
                if not has_explicit_butter and not has_explicit_quantity_in_text:
                    normalized.append(ParsedFoodPayload(name="butter", quantity=5, unit="grams"))
                continue

            if lowered_unit == "serving" and cls._contains_any_token(lowered_name, cls.TOAST_TOKENS):
                normalized.append(
                    ParsedFoodPayload(name=item.name, quantity=round(item.quantity * 40.0, 2), unit="grams")
                )
                continue

            if lowered_unit == "serving" and cls._contains_any_token(lowered_name, cls.MILK_TOKENS):
                normalized.append(
                    ParsedFoodPayload(name=item.name, quantity=round(item.quantity * 200.0, 2), unit="grams")
                )
                continue

            if lowered_unit == "serving" and cls._contains_any_token(lowered_name, cls.COFFEE_TOKENS):
                normalized.append(
                    ParsedFoodPayload(name="coffee", quantity=round(item.quantity * 240.0, 2), unit="grams")
                )
                continue

            if lowered_unit == "serving" and cls._contains_any_token(lowered_name, cls.SWEETENER_TOKENS):
                normalized.append(ParsedFoodPayload(name="sweetener", quantity=max(1.0, item.quantity), unit="grams"))
                continue

            if lowered_unit == "serving" and cls._contains_any_token(lowered_name, cls.BUTTER_TOKENS):
                normalized.append(ParsedFoodPayload(name="butter", quantity=round(item.quantity * 5.0, 2), unit="grams"))
                continue

            normalized.append(item)

        return normalized

    @classmethod
    def _resolve_item_nutrition(
        cls,
        db: Session,
        normalized_name: str,
        quantity: float,
        unit: str,
        nutrition_cache_by_name: dict[str, tuple[str, float, float, float, float, float]],
        portion_cache_by_food_and_unit: dict[tuple[str, str], float],
    ) -> tuple[str, float, float, float, float, float, float, float, float, float]:
        """
        Resolve nutrition for one parsed item and calculate totals.

        Returns:
            tuple(usda_fdc_id, quantity_grams, calories_per_100g, carbs_per_100g,
                  protein_per_100g, fat_per_100g, total_calories,
                  total_carbs, total_protein, total_fat)
        """
        if quantity <= 0:
            raise FoodServiceError("insufficient_data")

        parsed_unit = unit.strip().lower()

        # Defensive guard: avoid oversized "scrambled eggs" prepared-serving matches.
        if parsed_unit in cls.PORTION_UNITS and cls._contains_any_token(normalized_name, cls.SCRAMBLED_EGG_TOKENS):
            normalized_name = "egg"
            parsed_unit = "piece"
            quantity = quantity if quantity > 1 else 2.0

        if parsed_unit in cls.PORTION_UNITS and cls._contains_any_token(normalized_name, cls.BUTTER_TOKENS):
            normalized_name = "butter"
            parsed_unit = "grams"
            quantity = round(quantity * 5.0, 2)

        requires_serving_resolution = is_serving_unit(parsed_unit)

        cached_entry = (
            db.query(FoodEntry)
            .filter(FoodEntry.normalized_name == normalized_name)
            .order_by(FoodEntry.created_at.desc())
            .first()
        )

        serving_size_grams: float | None = None
        nutrition_source = "unknown"
        cached_nutrition = nutrition_cache_by_name.get(normalized_name)
        if cached_nutrition is not None:
            (
                usda_fdc_id,
                calories_per_100g,
                carbs_per_100g,
                protein_per_100g,
                fat_per_100g,
                cached_serving_grams,
            ) = cached_nutrition
            serving_size_grams = cached_serving_grams if cached_serving_grams > 0 else None
            nutrition_source = "memory_cache"
        else:
            try:
                fatsecret_match = search_fatsecret_food_by_name(normalized_name)
                usda_fdc_id = f"fatsecret:{fatsecret_match.food_id}"
                calories_per_100g = fatsecret_match.calories_per_100g
                carbs_per_100g = fatsecret_match.carbs_per_100g
                protein_per_100g = fatsecret_match.protein_per_100g
                fat_per_100g = fatsecret_match.fat_per_100g
                serving_size_grams = fatsecret_match.serving_size_grams
                nutrition_cache_by_name[normalized_name] = (
                    usda_fdc_id,
                    calories_per_100g,
                    carbs_per_100g,
                    protein_per_100g,
                    fat_per_100g,
                    serving_size_grams or 0.0,
                )
                nutrition_source = "fatsecret_search"
            except FatSecretServiceError:
                try:
                    usda_match = search_food_by_name(normalized_name)
                    usda_fdc_id = usda_match.fdc_id
                    calories_per_100g = usda_match.calories_per_100g
                    carbs_per_100g = usda_match.carbs_per_100g
                    protein_per_100g = usda_match.protein_per_100g
                    fat_per_100g = usda_match.fat_per_100g
                    serving_size_grams = usda_match.serving_size_grams
                    nutrition_cache_by_name[normalized_name] = (
                        usda_fdc_id,
                        calories_per_100g,
                        carbs_per_100g,
                        protein_per_100g,
                        fat_per_100g,
                        serving_size_grams or 0.0,
                    )
                    nutrition_source = "usda_search"
                except USDAServiceError as exc:
                # Fallback to latest cached calories if available.
                    if cached_entry is None:
                        raise FoodServiceError(str(exc)) from exc

                    usda_fdc_id = cached_entry.usda_fdc_id
                    calories_per_100g = float(cached_entry.calories_per_100g)
                    carbs_per_100g = 0.0
                    protein_per_100g = 0.0
                    fat_per_100g = 0.0
                    nutrition_source = "db_history_fallback"

        if parsed_unit in cls.FAST_LOCAL_CONVERSION_UNITS:
            try:
                quantity_grams = convert_to_grams(quantity, parsed_unit, normalized_name)
            except FoodParserError as exc:
                raise FoodServiceError(str(exc)) from exc
        elif requires_serving_resolution or parsed_unit in cls.PORTION_UNITS:
            cache_key = (normalized_name, parsed_unit)
            portion_grams = portion_cache_by_food_and_unit.get(cache_key)
            if portion_grams is None:
                portion_grams = PortionResolverService.resolve_portion_grams(
                    db=db,
                    food_name=normalized_name,
                    unit=parsed_unit,
                    preferred_serving_grams=serving_size_grams if requires_serving_resolution else None,
                )
                portion_cache_by_food_and_unit[cache_key] = portion_grams
            quantity_grams = round(quantity * portion_grams, 2)
        else:
            try:
                quantity_grams = convert_to_grams(quantity, parsed_unit, normalized_name)
            except FoodParserError as exc:
                raise FoodServiceError(str(exc)) from exc

        if quantity_grams <= 0:
            raise FoodServiceError("insufficient_data")

        total_calories = round((calories_per_100g / 100.0) * quantity_grams, 2)
        total_carbs = round((carbs_per_100g / 100.0) * quantity_grams, 2)
        total_protein = round((protein_per_100g / 100.0) * quantity_grams, 2)
        total_fat = round((fat_per_100g / 100.0) * quantity_grams, 2)

        logger.info(
            "resolve_item source=%s food=%s unit=%s qty=%.2f grams=%.2f",
            nutrition_source,
            normalized_name,
            parsed_unit,
            quantity,
            quantity_grams,
        )

        return (
            usda_fdc_id,
            quantity_grams,
            calories_per_100g,
            carbs_per_100g,
            protein_per_100g,
            fat_per_100g,
            total_calories,
            total_carbs,
            total_protein,
            total_fat,
        )

    @classmethod
    def parse_and_log_meals(cls, db: Session, user_id: int, text: str) -> FoodParseLogResponse:
        """
        Parse free-form meal text, split by meal type markers, compute item nutrition,
        log each item to daily nutrition totals, and return meal-separated distribution.
        """
        overall_start = perf_counter()
        sections = split_text_by_meal_type(text)
        if not sections:
            raise FoodServiceError("insufficient_data")

        meals_response: list[ParsedMealResponse] = []
        day_total_quantity_grams = 0.0
        day_total_calories = 0.0
        day_total_carbs = 0.0
        day_total_protein = 0.0
        day_total_fat = 0.0
        generic_meal_counter = 0
        nutrition_cache_by_name: dict[str, tuple[str, float, float, float, float, float]] = {}
        portion_cache_by_food_and_unit: dict[tuple[str, str], float] = {}

        for meal_type, segment_text in sections:
            meal_parse_start = perf_counter()
            try:
                parsed_items = parse_food_input(segment_text)
            except FoodParserError as exc:
                raise FoodServiceError(str(exc)) from exc

            parsed_items = cls._normalize_ambiguous_items(parsed_items, segment_text)
            logger.info(
                "parse_and_log stage=parse_food_input meal_type=%s items=%s duration_ms=%.2f",
                meal_type,
                len(parsed_items),
                (perf_counter() - meal_parse_start) * 1000,
            )

            meal_items: list[FoodItemDistributionResponse] = []
            meal_total_quantity_grams = 0.0
            meal_total_calories = 0.0
            meal_total_carbs = 0.0
            meal_total_protein = 0.0
            meal_total_fat = 0.0
            meal_timestamp: datetime | None = None

            meal_label = meal_label_for_type(meal_type)
            if meal_type == "meal":
                generic_meal_counter += 1
                meal_label = f"Comida {generic_meal_counter}"

            meal_group_id = uuid4().hex

            for parsed in parsed_items:
                resolve_start = perf_counter()
                normalized_name = parsed.name.strip().lower()
                if not normalized_name:
                    continue

                (
                    usda_fdc_id,
                    quantity_grams,
                    calories_per_100g,
                    carbs_per_100g,
                    protein_per_100g,
                    fat_per_100g,
                    total_calories,
                    total_carbs,
                    total_protein,
                    total_fat,
                ) = cls._resolve_item_nutrition(
                    db=db,
                    normalized_name=normalized_name,
                    quantity=parsed.quantity,
                    unit=parsed.unit,
                    nutrition_cache_by_name=nutrition_cache_by_name,
                    portion_cache_by_food_and_unit=portion_cache_by_food_and_unit,
                )
                logger.info(
                    "parse_and_log stage=resolve_item food=%s duration_ms=%.2f",
                    normalized_name,
                    (perf_counter() - resolve_start) * 1000,
                )

                db.add(
                    FoodEntry(
                        original_text=segment_text.strip(),
                        normalized_name=normalized_name,
                        quantity_grams=quantity_grams,
                        usda_fdc_id=usda_fdc_id,
                        calories_per_100g=calories_per_100g,
                        total_calories=total_calories,
                    )
                )

                logged_meal = NutritionService.log_meal(
                    db=db,
                    user_id=user_id,
                    meal_data=MealLogCreate(
                        meal_type=meal_type,
                        meal_group_id=meal_group_id,
                        meal_label=meal_label,
                        food_name=normalized_name,
                        quantity_grams=quantity_grams,
                        calories_per_100g=calories_per_100g,
                        carbs_per_100g=carbs_per_100g,
                        protein_per_100g=protein_per_100g,
                        fat_per_100g=fat_per_100g,
                    ),
                    auto_commit=False,
                )

                if meal_timestamp is None:
                    meal_timestamp = logged_meal.event_timestamp

                meal_items.append(
                    FoodItemDistributionResponse(
                        food=normalized_name,
                        quantity_grams=quantity_grams,
                        calories_per_100g=round(calories_per_100g, 2),
                        carbs_per_100g=round(carbs_per_100g, 2),
                        protein_per_100g=round(protein_per_100g, 2),
                        fat_per_100g=round(fat_per_100g, 2),
                        total_calories=round(total_calories, 2),
                        total_carbs=round(total_carbs, 2),
                        total_protein=round(total_protein, 2),
                        total_fat=round(total_fat, 2),
                    )
                )

                meal_total_quantity_grams += quantity_grams
                meal_total_calories += total_calories
                meal_total_carbs += total_carbs
                meal_total_protein += total_protein
                meal_total_fat += total_fat

            if not meal_items:
                continue

            if meal_timestamp is None:
                meal_timestamp = datetime.now(timezone.utc)

            meals_response.append(
                ParsedMealResponse(
                    meal_type=meal_type,
                    meal_label=meal_label,
                    meal_timestamp=meal_timestamp,
                    items=meal_items,
                    total_quantity_grams=round(meal_total_quantity_grams, 2),
                    total_calories=round(meal_total_calories, 2),
                    total_carbs=round(meal_total_carbs, 2),
                    total_protein=round(meal_total_protein, 2),
                    total_fat=round(meal_total_fat, 2),
                )
            )

            day_total_quantity_grams += meal_total_quantity_grams
            day_total_calories += meal_total_calories
            day_total_carbs += meal_total_carbs
            day_total_protein += meal_total_protein
            day_total_fat += meal_total_fat

        if not meals_response:
            raise FoodServiceError("insufficient_data")

        db.commit()
        logger.info(
            "parse_and_log stage=total meals=%s duration_ms=%.2f",
            len(meals_response),
            (perf_counter() - overall_start) * 1000,
        )

        return FoodParseLogResponse(
            meals=meals_response,
            total_quantity_grams=round(day_total_quantity_grams, 2),
            total_calories=round(day_total_calories, 2),
            total_carbs=round(day_total_carbs, 2),
            total_protein=round(day_total_protein, 2),
            total_fat=round(day_total_fat, 2),
        )

    @classmethod
    def parse_and_calculate(cls, db: Session, text: str) -> FoodParseCalculateResponse:
        overall_start = perf_counter()
        try:
            parsed_items = parse_food_input(text)
        except FoodParserError as exc:
            raise FoodServiceError(str(exc)) from exc

        parsed_items = cls._normalize_ambiguous_items(parsed_items, text)
        logger.info(
            "parse_and_calculate stage=parse_food_input items=%s duration_ms=%.2f",
            len(parsed_items),
            (perf_counter() - overall_start) * 1000,
        )

        aggregate_quantity_grams = 0.0
        aggregate_total_calories = 0.0
        aggregate_total_carbs = 0.0
        aggregate_total_protein = 0.0
        aggregate_total_fat = 0.0
        normalized_names: list[str] = []
        usda_ids: list[str] = []
        nutrition_cache_by_name: dict[str, tuple[str, float, float, float, float, float]] = {}
        portion_cache_by_food_and_unit: dict[tuple[str, str], float] = {}

        for parsed in parsed_items:
            normalized_name = parsed.name.strip().lower()
            if not normalized_name:
                continue

            (
                usda_fdc_id,
                quantity_grams,
                _calories_per_100g,
                _carbs_per_100g,
                _protein_per_100g,
                _fat_per_100g,
                total_calories,
                total_carbs,
                total_protein,
                total_fat,
            ) = cls._resolve_item_nutrition(
                db=db,
                normalized_name=normalized_name,
                quantity=parsed.quantity,
                unit=parsed.unit,
                nutrition_cache_by_name=nutrition_cache_by_name,
                portion_cache_by_food_and_unit=portion_cache_by_food_and_unit,
            )

            normalized_names.append(normalized_name)
            usda_ids.append(usda_fdc_id)

            aggregate_quantity_grams += quantity_grams
            aggregate_total_calories += total_calories
            aggregate_total_carbs += total_carbs
            aggregate_total_protein += total_protein
            aggregate_total_fat += total_fat

        response = cls._persist_aggregate_calculation(
            db=db,
            original_text=text,
            normalized_names=normalized_names,
            source_ids=usda_ids,
            aggregate_quantity_grams=aggregate_quantity_grams,
            aggregate_total_calories=aggregate_total_calories,
            aggregate_total_carbs=aggregate_total_carbs,
            aggregate_total_protein=aggregate_total_protein,
            aggregate_total_fat=aggregate_total_fat,
        )
        logger.info(
            "parse_and_calculate stage=final source=parser_pipeline duration_ms=%.2f",
            (perf_counter() - overall_start) * 1000,
        )
        return response
