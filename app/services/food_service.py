from sqlalchemy.orm import Session

from ..models.food import FoodEntry
from ..schemas.food import FoodParseCalculateResponse
from .food_parser import FoodParserError, convert_to_grams, is_serving_unit, parse_food_input
from .usda_service import USDAServiceError, search_food_by_name


class FoodServiceError(Exception):
    """Base exception for food service workflow errors."""


class FoodService:
    """Service layer for food parsing, USDA lookup, caching, and calorie calculation."""

    DEFAULT_SERVING_GRAMS = 100.0

    @classmethod
    def parse_and_calculate(cls, db: Session, text: str) -> FoodParseCalculateResponse:
        try:
            parsed = parse_food_input(text)
        except FoodParserError as exc:
            raise FoodServiceError(str(exc)) from exc

        normalized_name = parsed.name.strip().lower()
        if parsed.quantity is None or parsed.quantity <= 0:
            raise FoodServiceError("insufficient_data")

        parsed_unit = parsed.unit.strip().lower()
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
        else:
            try:
                usda_match = search_food_by_name(normalized_name)
            except USDAServiceError as exc:
                raise FoodServiceError(str(exc)) from exc

            usda_fdc_id = usda_match.fdc_id
            calories_per_100g = usda_match.calories_per_100g

        if requires_serving_resolution:
            serving_size_grams = usda_match.serving_size_grams if usda_match else None
            if serving_size_grams is None:
                serving_size_grams = cls.DEFAULT_SERVING_GRAMS
            quantity_grams = round(parsed.quantity * serving_size_grams, 2)
        else:
            try:
                quantity_grams = convert_to_grams(parsed.quantity, parsed_unit)
            except FoodParserError as exc:
                raise FoodServiceError(str(exc)) from exc

        if quantity_grams <= 0:
            raise FoodServiceError("insufficient_data")

        total_calories = round((calories_per_100g / 100.0) * quantity_grams, 2)

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
            total_calories=total_calories,
        )
