from typing import Any
import re

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

MEAL_KEYWORDS_TO_TYPE: dict[str, str] = {
    "desayuno": "breakfast",
    "desayune": "breakfast",
    "desayuné": "breakfast",
    "almuerzo": "lunch",
    "almorce": "lunch",
    "almorcé": "lunch",
    "cena": "dinner",
    "cene": "dinner",
    "cené": "dinner",
    "merienda": "snack",
    "snack": "snack",
    "colacion": "snack",
    "colación": "snack",
}

MEAL_TYPE_LABELS: dict[str, str] = {
    "breakfast": "Desayuno",
    "lunch": "Almuerzo",
    "dinner": "Cena",
    "snack": "Snack",
    "meal": "Comida",
}

MEAL_SPLIT_PATTERN = re.compile(
    r"\b(desayuno|desayune|desayuné|almuerzo|almorce|almorcé|cena|cene|cené|merienda|snack|colacion|colación)\b",
    re.IGNORECASE,
)

TEMPORAL_SPLIT_PATTERN = re.compile(r"\b(despues|después|luego)\b", re.IGNORECASE)
POSTRE_PREFIX_PATTERN = re.compile(r"^(?:de\s+)?postre\b", re.IGNORECASE)



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


def meal_label_for_type(meal_type: str) -> str:
    """Return localized display label for a normalized meal type."""
    return MEAL_TYPE_LABELS.get(meal_type, "Comida")


def _cleanup_segment(text: str) -> str:
    """Normalize segmented text by removing dangling connectors around boundaries."""
    cleaned = text.strip(" ,.;:-")
    cleaned = re.sub(r"^(?:y|e)\s+", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+(?:y|e)$", "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip(" ,.;:-")


def _split_by_temporal_markers(text: str) -> list[str]:
    """Split a segment by temporal connectors (después/luego), except dessert continuations."""
    cleaned = _cleanup_segment(text)
    if not cleaned:
        return []

    chunks: list[str] = []
    start = 0
    matches = list(TEMPORAL_SPLIT_PATTERN.finditer(cleaned))

    for match in matches:
        tail = cleaned[match.end() :].lstrip(" ,.;:-")
        # Keep dessert attached to the same meal context.
        if POSTRE_PREFIX_PATTERN.match(tail):
            continue

        chunk = _cleanup_segment(cleaned[start : match.start()])
        if chunk:
            chunks.append(chunk)
        start = match.end()

    final_chunk = _cleanup_segment(cleaned[start:])
    if final_chunk:
        chunks.append(final_chunk)

    return chunks


def split_text_by_meal_type(text: str) -> list[tuple[str, str]]:
    """
    Split free-form text by detected meal markers (desayuno, almuerzo, cena, snack).

    Returns a list of (meal_type, section_text). Falls back to single generic meal.
    """
    cleaned = text.strip()
    if not cleaned:
        return []

    matches = list(MEAL_SPLIT_PATTERN.finditer(cleaned))
    if not matches:
        temporal_chunks = _split_by_temporal_markers(cleaned)
        if not temporal_chunks:
            return [("meal", cleaned)]
        return [("meal", chunk) for chunk in temporal_chunks]

    sections: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        raw_keyword = match.group(0).lower()
        meal_type = MEAL_KEYWORDS_TO_TYPE.get(raw_keyword, "meal")

        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(cleaned)
        segment = cleaned[start:end].strip(" ,.;:-")

        if not segment:
            continue

        temporal_chunks = _split_by_temporal_markers(segment)
        if not temporal_chunks:
            continue

        for chunk_index, chunk in enumerate(temporal_chunks):
            normalized_meal_type = meal_type if chunk_index == 0 else "meal"
            sections.append((normalized_meal_type, chunk))

    if not sections:
        return [("meal", cleaned)]

    return sections


def parse_food_input(text: str) -> list[ParsedFoodPayload]:
    """
    Parse natural language food input to structured data using strict JSON contract.

    Raises FoodParserError when parsing fails or response is malformed.
    """
    if not text or not text.strip():
        raise FoodParserError("insufficient_data")

    try:
        data: Any = parse_food_with_gemini(text)
    except AIParserError as exc:
        raise FoodParserError(str(exc)) from exc

    if isinstance(data, dict) and data.get("error"):
        if data.get("error") == "invalid_domain":
            raise FoodParserError("invalid_domain")
        if data.get("error") == "insufficient_data":
            raise FoodParserError("insufficient_data")
        raise FoodParserError("malformed_parser_response")

    raw_items: list[Any]
    if isinstance(data, list):
        raw_items = data
    elif isinstance(data, dict) and isinstance(data.get("items"), list):
        raw_items = data.get("items", [])
    elif isinstance(data, dict):
        raw_items = [data]
    else:
        raise FoodParserError("malformed_parser_response")

    if not raw_items:
        raise FoodParserError("insufficient_data")

    parsed_items: list[ParsedFoodPayload] = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        try:
            parsed_items.append(ParsedFoodPayload(**item))
        except Exception:
            continue

    if not parsed_items:
        raise FoodParserError("malformed_parser_response")

    return parsed_items
