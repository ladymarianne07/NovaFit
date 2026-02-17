from sqlalchemy.orm import Session
from datetime import datetime, timezone

from ..models.food import FoodEntry
from ..schemas.food import (
    FoodItemDistributionResponse,
    FoodParseCalculateResponse,
    FoodParseLogResponse,
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
from .usda_service import USDAServiceError, search_food_by_name


class FoodServiceError(Exception):
    """Base exception for food service workflow errors."""


class FoodService:
    """Service layer for food parsing, USDA lookup, caching, and nutrition calculation."""

    DEFAULT_SERVING_GRAMS = 100.0

    @classmethod
    def _resolve_item_nutrition(
        cls,
        db: Session,
        normalized_name: str,
        quantity: float,
        unit: str,
    ) -> tuple[str, float, float, float, float, float, float, float, float, float]:
        """
        Resolve USDA nutrition for one parsed item and calculate totals.

        Returns:
            tuple(usda_fdc_id, quantity_grams, calories_per_100g, carbs_per_100g,
                  protein_per_100g, fat_per_100g, total_calories,
                  total_carbs, total_protein, total_fat)
        """
        if quantity <= 0:
            raise FoodServiceError("insufficient_data")

        parsed_unit = unit.strip().lower()
        requires_serving_resolution = is_serving_unit(parsed_unit)

        cached_entry = (
            db.query(FoodEntry)
            .filter(FoodEntry.normalized_name == normalized_name)
            .order_by(FoodEntry.created_at.desc())
            .first()
        )

        usda_match = None
        if cached_entry and not requires_serving_resolution:
            usda_fdc_id = cached_entry.usda_fdc_id
            calories_per_100g = float(cached_entry.calories_per_100g)
            carbs_per_100g = 0.0
            protein_per_100g = 0.0
            fat_per_100g = 0.0

            try:
                usda_match = search_food_by_name(normalized_name)
                carbs_per_100g = usda_match.carbs_per_100g
                protein_per_100g = usda_match.protein_per_100g
                fat_per_100g = usda_match.fat_per_100g
            except USDAServiceError:
                pass
        else:
            try:
                usda_match = search_food_by_name(normalized_name)
            except USDAServiceError as exc:
                raise FoodServiceError(str(exc)) from exc

            usda_fdc_id = usda_match.fdc_id
            calories_per_100g = usda_match.calories_per_100g
            carbs_per_100g = usda_match.carbs_per_100g
            protein_per_100g = usda_match.protein_per_100g
            fat_per_100g = usda_match.fat_per_100g

        if requires_serving_resolution:
            serving_size_grams = usda_match.serving_size_grams if usda_match else None
            if serving_size_grams is None:
                serving_size_grams = cls.DEFAULT_SERVING_GRAMS
            quantity_grams = round(quantity * serving_size_grams, 2)
        else:
            try:
                quantity_grams = convert_to_grams(quantity, parsed_unit)
            except FoodParserError as exc:
                raise FoodServiceError(str(exc)) from exc

        if quantity_grams <= 0:
            raise FoodServiceError("insufficient_data")

        total_calories = round((calories_per_100g / 100.0) * quantity_grams, 2)
        total_carbs = round((carbs_per_100g / 100.0) * quantity_grams, 2)
        total_protein = round((protein_per_100g / 100.0) * quantity_grams, 2)
        total_fat = round((fat_per_100g / 100.0) * quantity_grams, 2)

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

        for meal_type, segment_text in sections:
            try:
                parsed_items = parse_food_input(segment_text)
            except FoodParserError as exc:
                raise FoodServiceError(str(exc)) from exc

            meal_items: list[FoodItemDistributionResponse] = []
            meal_total_quantity_grams = 0.0
            meal_total_calories = 0.0
            meal_total_carbs = 0.0
            meal_total_protein = 0.0
            meal_total_fat = 0.0
            meal_timestamp: datetime | None = None

            for parsed in parsed_items:
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
                        food_name=normalized_name,
                        quantity_grams=quantity_grams,
                        calories_per_100g=calories_per_100g,
                        carbs_per_100g=carbs_per_100g,
                        protein_per_100g=protein_per_100g,
                        fat_per_100g=fat_per_100g,
                    ),
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

            meal_label = meal_label_for_type(meal_type)
            if meal_type == "meal":
                generic_meal_counter += 1
                meal_label = f"Comida {generic_meal_counter}"

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
        try:
            parsed_items = parse_food_input(text)
        except FoodParserError as exc:
            raise FoodServiceError(str(exc)) from exc

        aggregate_quantity_grams = 0.0
        aggregate_total_calories = 0.0
        aggregate_total_carbs = 0.0
        aggregate_total_protein = 0.0
        aggregate_total_fat = 0.0
        normalized_names: list[str] = []
        usda_ids: list[str] = []

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
            )

            normalized_names.append(normalized_name)
            usda_ids.append(usda_fdc_id)

            aggregate_quantity_grams += quantity_grams
            aggregate_total_calories += total_calories
            aggregate_total_carbs += total_carbs
            aggregate_total_protein += total_protein
            aggregate_total_fat += total_fat

        if aggregate_quantity_grams <= 0:
            raise FoodServiceError("insufficient_data")

        calories_per_100g = round((aggregate_total_calories / aggregate_quantity_grams) * 100.0, 2)
        carbs_per_100g = round((aggregate_total_carbs / aggregate_quantity_grams) * 100.0, 2)
        protein_per_100g = round((aggregate_total_protein / aggregate_quantity_grams) * 100.0, 2)
        fat_per_100g = round((aggregate_total_fat / aggregate_quantity_grams) * 100.0, 2)

        normalized_name = " + ".join(dict.fromkeys(normalized_names))
        usda_fdc_id = usda_ids[0] if len(usda_ids) == 1 else "multi"

        total_calories = round(aggregate_total_calories, 2)
        total_carbs = round(aggregate_total_carbs, 2)
        total_protein = round(aggregate_total_protein, 2)
        total_fat = round(aggregate_total_fat, 2)
        quantity_grams = round(aggregate_quantity_grams, 2)

        food_entry = FoodEntry(
            original_text=text.strip(),
            normalized_name=normalized_name,
            quantity_grams=quantity_grams,
            usda_fdc_id=usda_fdc_id,
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
