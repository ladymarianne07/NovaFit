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

PORTION_UNIT_TO_GRAMS_GENERIC: dict[str, float] = {
    "ml": 1.0,
    "cup": 240.0,
    "cups": 240.0,
    "taza": 240.0,
    "tazas": 240.0,
    "tablespoon": 15.0,
    "tablespoons": 15.0,
    "tbsp": 15.0,
    "cucharada": 15.0,
    "cucharadas": 15.0,
    "teaspoon": 5.0,
    "teaspoons": 5.0,
    "tsp": 5.0,
    "cucharadita": 5.0,
    "cucharaditas": 5.0,
}

FOOD_SPECIFIC_PORTION_GRAMS: dict[str, dict[str, float]] = {
    "coffee": {"cup": 240.0, "tablespoon": 15.0, "teaspoon": 5.0, "ml": 1.0},
    "cafe": {"cup": 240.0, "tablespoon": 15.0, "teaspoon": 5.0, "ml": 1.0},
    "milk": {"cup": 244.0, "tablespoon": 15.3, "teaspoon": 5.1, "ml": 1.03},
    "leche": {"cup": 244.0, "tablespoon": 15.3, "teaspoon": 5.1, "ml": 1.03},
}

DEFAULT_SERVING_GRAMS_BY_KEYWORD: dict[str, float] = {
    "coffee": 240.0,
    "cafe": 240.0,
    "milk": 244.0,
    "leche": 244.0,
    "egg": 50.0,
    "huevo": 50.0,
    "bread": 30.0,
    "pan": 30.0,
}

SERVING_UNITS: set[str] = {
    "serving",
    "portion",
    "porción",
    "porcion",
}

COMPOSITE_CONNECTOR_PATTERN = re.compile(r"\b(with|con|and|y|e)\b|[+&/]", re.IGNORECASE)
COFFEE_WITH_MILK_PATTERN = re.compile(r"\b(cafe|café|coffee)\b.*\b(leche|milk)\b", re.IGNORECASE)
CONNECTOR_TOKENS = {"with", "con", "and", "y", "e"}

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

ITEM_CONTAINER_KEYS: tuple[str, ...] = (
    "items",
    "foods",
    "food_items",
    "alimentos",
)

NESTED_CONTAINER_KEYS: tuple[str, ...] = (
    "meals",
    "comidas",
)



def _normalize_unit(unit: str) -> str:
    normalized = unit.strip().lower()

    aliases = {
        "cup": "cup",
        "cups": "cup",
        "taza": "cup",
        "tazas": "cup",
        "tbsp": "tablespoon",
        "tablespoon": "tablespoon",
        "tablespoons": "tablespoon",
        "cucharada": "tablespoon",
        "cucharadas": "tablespoon",
        "tsp": "teaspoon",
        "teaspoon": "teaspoon",
        "teaspoons": "teaspoon",
        "cucharadita": "teaspoon",
        "cucharaditas": "teaspoon",
        "ml": "ml",
    }

    return aliases.get(normalized, normalized)


def _food_specific_multiplier(food_name: str, normalized_unit: str) -> float | None:
    lowered_name = food_name.lower().strip()
    for keyword, mapping in FOOD_SPECIFIC_PORTION_GRAMS.items():
        if keyword in lowered_name and normalized_unit in mapping:
            return mapping[normalized_unit]
    return None


def estimate_serving_grams(food_name: str, default_value: float = 100.0) -> float:
    """Estimate serving grams for foods when external source has no serving size."""
    lowered_name = food_name.lower().strip()
    for keyword, grams in DEFAULT_SERVING_GRAMS_BY_KEYWORD.items():
        if keyword in lowered_name:
            return grams
    return default_value


def convert_to_grams(quantity: float, unit: str, food_name: str | None = None) -> float:
    """Convert quantity from supported unit to grams with food-aware portion defaults."""
    normalized_unit = _normalize_unit(unit)

    weight_multiplier = UNIT_TO_GRAMS.get(normalized_unit)
    if weight_multiplier is not None:
        return round(quantity * weight_multiplier, 2)

    if food_name:
        specific_multiplier = _food_specific_multiplier(food_name, normalized_unit)
        if specific_multiplier is not None:
            return round(quantity * specific_multiplier, 2)

    generic_multiplier = PORTION_UNIT_TO_GRAMS_GENERIC.get(normalized_unit)
    if generic_multiplier is not None:
        return round(quantity * generic_multiplier, 2)

    raise FoodParserError("unsupported_unit")


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


def _collect_food_item_candidates(node: Any) -> list[dict[str, Any]]:
    """Recursively collect probable food item dictionaries from heterogeneous AI JSON."""
    collected: list[dict[str, Any]] = []

    if isinstance(node, list):
        for child in node:
            collected.extend(_collect_food_item_candidates(child))
        return collected

    if not isinstance(node, dict):
        return collected

    has_item_shape = all(field in node for field in ("name", "quantity", "unit"))
    if has_item_shape:
        collected.append(node)

    for key in ITEM_CONTAINER_KEYS:
        value = node.get(key)
        if isinstance(value, list):
            collected.extend(_collect_food_item_candidates(value))

    for key in NESTED_CONTAINER_KEYS:
        value = node.get(key)
        if isinstance(value, list):
            collected.extend(_collect_food_item_candidates(value))

    return collected


def _split_composite_food_name(name: str) -> list[str]:
    raw_parts = COMPOSITE_CONNECTOR_PATTERN.split(name)
    parts = [
        part.strip(" ,.;:-")
        for part in raw_parts
        if part and part.strip(" ,.;:-") and part.strip(" ,.;:-").lower() not in CONNECTOR_TOKENS
    ]
    if len(parts) <= 1:
        return [name.strip()]
    return parts


def _expand_composite_item(item: ParsedFoodPayload) -> list[ParsedFoodPayload]:
    name = item.name.strip()
    if not name:
        return []

    # High-priority beverage case: coffee with milk -> split into half cup + half cup.
    if COFFEE_WITH_MILK_PATTERN.search(name) and is_serving_unit(item.unit):
        half_quantity = round(item.quantity * 0.5, 4)
        return [
            ParsedFoodPayload(name="coffee", quantity=half_quantity, unit="cup"),
            ParsedFoodPayload(name="milk", quantity=half_quantity, unit="cup"),
        ]

    parts = _split_composite_food_name(name)
    if len(parts) == 1:
        return [item]

    each_quantity = round(item.quantity / len(parts), 4)
    expanded: list[ParsedFoodPayload] = []
    for part in parts:
        if not part:
            continue
        expanded.append(
            ParsedFoodPayload(
                name=part,
                quantity=each_quantity,
                unit=item.unit,
            )
        )

    return expanded or [item]


def _has_explicit_quantity(text: str) -> bool:
    return bool(re.search(r"\d", text))


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

    raw_items = _collect_food_item_candidates(data)
    if not raw_items:
        raise FoodParserError("malformed_parser_response")

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

    expanded_items: list[ParsedFoodPayload] = []
    for parsed_item in parsed_items:
        expanded_items.extend(_expand_composite_item(parsed_item))

    if not expanded_items:
        raise FoodParserError("malformed_parser_response")

    # Deterministic default for plain "coffee with milk" without explicit quantities.
    if COFFEE_WITH_MILK_PATTERN.search(text) and not _has_explicit_quantity(text):
        normalized_items: list[ParsedFoodPayload] = []
        has_coffee_or_milk = False

        for item in expanded_items:
            lowered = item.name.lower().strip()
            if "coffee" in lowered or "cafe" in lowered or "café" in lowered or "milk" in lowered or "leche" in lowered:
                has_coffee_or_milk = True
                continue
            normalized_items.append(item)

        if has_coffee_or_milk:
            return [
                ParsedFoodPayload(name="coffee", quantity=0.5, unit="cup"),
                ParsedFoodPayload(name="milk", quantity=0.5, unit="cup"),
            ] + normalized_items

        if len(expanded_items) == 1:
            return [
                ParsedFoodPayload(name="coffee", quantity=0.5, unit="cup"),
                ParsedFoodPayload(name="milk", quantity=0.5, unit="cup"),
            ]

    return expanded_items
