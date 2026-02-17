from typing import Any

from ..schemas.food import ParsedFoodPayload
from .ai_parser_service import AIParserError, parse_food_with_gemini


class FoodParserError(Exception):
    """Raised when parser cannot produce valid structured food data."""


UNIT_TO_GRAMS: dict[str, float] = {
    "g": 1.0,
    "gram": 1.0,
    "grams": 1.0,
    "gramo": 1.0,
    "gramos": 1.0,
    "kg": 1000.0,
    "kilogram": 1000.0,
    "kilograms": 1000.0,
    "kilogramo": 1000.0,
    "kilogramos": 1000.0,
    "oz": 28.3495,
    "onza": 28.3495,
    "onzas": 28.3495,
    "lb": 453.592,
    "lbs": 453.592,
    "libra": 453.592,
    "libras": 453.592,
}

SERVING_UNITS: set[str] = {
    "serving",
    "portion",
    "porción",
    "porcion",
}



def convert_to_grams(quantity: float, unit: str) -> float:
    """Convert quantity from supported unit to grams."""
    normalized_unit = unit.strip().lower()
    multiplier = UNIT_TO_GRAMS.get(normalized_unit)
    if multiplier is None:
        raise FoodParserError("unsupported_unit")
    return round(quantity * multiplier, 2)


def is_serving_unit(unit: str) -> bool:
    """Return True when unit represents one or more servings/portions."""
    return unit.strip().lower() in SERVING_UNITS


def parse_food_input(text: str) -> ParsedFoodPayload:
    """
    Parse natural language food input to structured data using strict JSON contract.

    Raises FoodParserError when parsing fails or response is malformed.
    """
    if not text or not text.strip():
        raise FoodParserError("insufficient_data")

    try:
        data: dict[str, Any] = parse_food_with_gemini(text)
    except AIParserError as exc:
        raise FoodParserError(str(exc)) from exc

    if data.get("error"):
        if data.get("error") == "invalid_domain":
            raise FoodParserError("invalid_domain")
        if data.get("error") == "insufficient_data":
            raise FoodParserError("insufficient_data")
        raise FoodParserError("malformed_parser_response")

    try:
        parsed = ParsedFoodPayload(**data)
    except Exception as exc:
        raise FoodParserError("malformed_parser_response") from exc

    return parsed
