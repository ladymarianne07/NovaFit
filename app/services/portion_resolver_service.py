from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable

import httpx
from rapidfuzz import fuzz
from sqlalchemy.orm import Session

from ..config import settings
from ..models.food_portion_cache import FoodPortionCache


logger = logging.getLogger(__name__)

USDA_SEARCH_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"
USDA_DETAIL_URL = "https://api.nal.usda.gov/fdc/v1/food/{fdc_id}"
FATSECRET_OAUTH_URL = "https://oauth.fatsecret.com/connect/token"
FATSECRET_API_URL = "https://platform.fatsecret.com/rest/server.api"
OPENFOODFACTS_SEARCH_URL = "https://world.openfoodfacts.org/cgi/search.pl"


@dataclass
class PortionResolution:
    grams_per_unit: float
    source: str
    confidence_score: float
    category: str | None = None


class PortionResolverService:
    """Resolve grams-per-unit from external sources with persistent caching."""

    REQUEST_TIMEOUT_SECONDS = 8.0
    USDA_CONFIDENCE = 0.90
    FATSECRET_CONFIDENCE = 0.80
    OPENFOODFACTS_CONFIDENCE = 0.70
    FALLBACK_CONFIDENCE = 0.45

    WEIGHT_UNITS = {
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
    }

    UNIT_ALIASES = {
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
        "serving": "serving",
        "portion": "serving",
        "porcion": "serving",
        "porción": "serving",
        "unit": "piece",
        "unidad": "piece",
        "piece": "piece",
        "pieza": "piece",
        "ml": "ml",
    }

    UNIT_TOKEN_MATCH = {
        "cup": {"cup", "cups", "taza", "tazas"},
        "tablespoon": {"tablespoon", "tablespoons", "tbsp", "cucharada", "cucharadas"},
        "teaspoon": {"teaspoon", "teaspoons", "tsp", "cucharadita", "cucharaditas"},
        "piece": {"piece", "pieces", "unidad", "unidades", "pieza", "piezas"},
        "serving": {"serving", "portion", "porcion", "porción"},
    }

    CATEGORY_KEYWORDS: dict[str, set[str]] = {
        "beverage": {"coffee", "cafe", "café", "tea", "té", "water", "juice", "jugo", "mate"},
        "dairy": {"milk", "leche", "yogurt", "yoghurt", "queso", "cheese"},
        "oil_fat": {"oil", "aceite", "butter", "manteca", "margarine", "ghee"},
        "grain_cooked": {"rice", "arroz", "pasta", "quinoa", "oat", "avena", "bread", "pan"},
        "protein_animal": {"chicken", "pollo", "beef", "carne", "fish", "pescado", "egg", "huevo"},
        "fruit": {"banana", "apple", "manzana", "orange", "naranja", "fruta"},
        "vegetable": {"salad", "ensalada", "tomato", "tomate", "broccoli", "brócoli", "zanahoria"},
    }

    CATEGORY_FALLBACK_GRAMS: dict[str, dict[str, float]] = {
        "beverage": {"serving": 240.0, "cup": 240.0, "tablespoon": 15.0, "teaspoon": 5.0, "piece": 240.0, "ml": 1.0},
        "dairy": {"serving": 200.0, "cup": 244.0, "tablespoon": 15.0, "teaspoon": 5.0, "piece": 30.0, "ml": 1.03},
        "oil_fat": {"serving": 14.0, "cup": 218.0, "tablespoon": 14.0, "teaspoon": 4.5, "piece": 14.0, "ml": 0.92},
        "grain_cooked": {"serving": 150.0, "cup": 158.0, "tablespoon": 10.0, "teaspoon": 3.3, "piece": 40.0, "ml": 0.8},
        "protein_animal": {"serving": 120.0, "cup": 140.0, "tablespoon": 15.0, "teaspoon": 5.0, "piece": 50.0, "ml": 1.0},
        "fruit": {"serving": 140.0, "cup": 150.0, "tablespoon": 10.0, "teaspoon": 3.5, "piece": 120.0, "ml": 0.95},
        "vegetable": {"serving": 100.0, "cup": 130.0, "tablespoon": 8.0, "teaspoon": 3.0, "piece": 80.0, "ml": 0.9},
        "generic": {"serving": 100.0, "cup": 240.0, "tablespoon": 15.0, "teaspoon": 5.0, "piece": 50.0, "ml": 1.0},
    }

    @classmethod
    def normalize_unit(cls, unit: str) -> str:
        return cls.UNIT_ALIASES.get(unit.strip().lower(), unit.strip().lower())

    @classmethod
    def resolve_portion_grams(
        cls,
        db: Session,
        food_name: str,
        unit: str,
        preferred_serving_grams: float | None = None,
    ) -> float:
        normalized_name = food_name.strip().lower()
        normalized_unit = cls.normalize_unit(unit)

        if not normalized_name:
            return cls.CATEGORY_FALLBACK_GRAMS["generic"].get(normalized_unit, 100.0)

        cached = cls._get_cached_resolution(db, normalized_name, normalized_unit)
        if cached is not None:
            return cached.grams_per_unit

        if normalized_unit == "serving" and preferred_serving_grams and preferred_serving_grams > 0:
            resolution = PortionResolution(
                grams_per_unit=float(preferred_serving_grams),
                source="usda",
                confidence_score=cls.USDA_CONFIDENCE,
                category=cls._detect_category(normalized_name),
            )
            cls._upsert_cache(db, normalized_name, normalized_unit, resolution)
            return resolution.grams_per_unit

        providers: list[tuple[str, callable]] = [
            ("usda", cls._resolve_from_usda),
            ("fatsecret", cls._resolve_from_fatsecret),
            ("openfoodfacts", cls._resolve_from_openfoodfacts),
        ]

        for _, resolver in providers:
            resolution = resolver(normalized_name, normalized_unit)
            if resolution is None:
                continue
            cls._upsert_cache(db, normalized_name, normalized_unit, resolution)
            return resolution.grams_per_unit

        category = cls._detect_category(normalized_name)
        fallback_value = cls._category_fallback_grams(category, normalized_unit)
        fallback_resolution = PortionResolution(
            grams_per_unit=fallback_value,
            source="category_fallback",
            confidence_score=cls.FALLBACK_CONFIDENCE,
            category=category,
        )
        cls._upsert_cache(db, normalized_name, normalized_unit, fallback_resolution)
        return fallback_value

    @classmethod
    def _get_cached_resolution(
        cls,
        db: Session,
        normalized_name: str,
        normalized_unit: str,
    ) -> PortionResolution | None:
        cached = (
            db.query(FoodPortionCache)
            .filter(
                FoodPortionCache.normalized_name == normalized_name,
                FoodPortionCache.unit_normalized == normalized_unit,
            )
            .order_by(FoodPortionCache.updated_at.desc().nullslast(), FoodPortionCache.created_at.desc())
            .first()
        )

        if cached is None:
            return None

        return PortionResolution(
            grams_per_unit=float(cached.grams_per_unit),
            source=str(cached.source),
            confidence_score=float(cached.confidence_score),
            category=str(cached.category) if cached.category else None,
        )

    @classmethod
    def _upsert_cache(
        cls,
        db: Session,
        normalized_name: str,
        normalized_unit: str,
        resolution: PortionResolution,
    ) -> None:
        existing = (
            db.query(FoodPortionCache)
            .filter(
                FoodPortionCache.normalized_name == normalized_name,
                FoodPortionCache.unit_normalized == normalized_unit,
            )
            .first()
        )

        if existing is None:
            db.add(
                FoodPortionCache(
                    normalized_name=normalized_name,
                    unit_normalized=normalized_unit,
                    grams_per_unit=resolution.grams_per_unit,
                    source=resolution.source,
                    confidence_score=resolution.confidence_score,
                    category=resolution.category,
                )
            )
        else:
            existing.grams_per_unit = resolution.grams_per_unit
            existing.source = resolution.source
            existing.confidence_score = resolution.confidence_score
            existing.category = resolution.category
            existing.updated_at = datetime.now(timezone.utc)

    @classmethod
    def _resolve_from_usda(cls, normalized_name: str, normalized_unit: str) -> PortionResolution | None:
        if not settings.USDA_API_KEY:
            return None

        payload: dict[str, Any] = {"query": normalized_name, "pageSize": 5}

        try:
            response = httpx.post(
                USDA_SEARCH_URL,
                params={"api_key": settings.USDA_API_KEY},
                json=payload,
                timeout=cls.REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
        except httpx.HTTPError:
            return None

        data = response.json()
        foods = data.get("foods", []) if isinstance(data, dict) else []
        if not isinstance(foods, list) or not foods:
            return None

        best_foods = sorted(
            [food for food in foods if isinstance(food, dict)],
            key=lambda item: fuzz.partial_token_set_ratio(normalized_name, str(item.get("description", ""))),
            reverse=True,
        )[:3]

        for food in best_foods:
            serving_size = cls._to_float(food.get("servingSize"))
            serving_unit = str(food.get("servingSizeUnit", "")).strip().lower()

            if normalized_unit == "serving" and serving_size and serving_unit in {"g", "gram", "grams", "gm"}:
                return PortionResolution(serving_size, "usda", cls.USDA_CONFIDENCE, cls._detect_category(normalized_name))

            fdc_id = str(food.get("fdcId", "")).strip()
            if not fdc_id:
                continue

            detail_resolution = cls._resolve_usda_from_food_portions(fdc_id, normalized_name, normalized_unit)
            if detail_resolution is not None:
                return detail_resolution

        return None

    @classmethod
    def _resolve_usda_from_food_portions(
        cls,
        fdc_id: str,
        normalized_name: str,
        normalized_unit: str,
    ) -> PortionResolution | None:
        try:
            response = httpx.get(
                USDA_DETAIL_URL.format(fdc_id=fdc_id),
                params={"api_key": settings.USDA_API_KEY},
                timeout=cls.REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
        except httpx.HTTPError:
            return None

        detail = response.json()
        portions = detail.get("foodPortions", []) if isinstance(detail, dict) else []
        if not isinstance(portions, list):
            return None

        for portion in portions:
            if not isinstance(portion, dict):
                continue

            gram_weight = cls._to_float(portion.get("gramWeight"))
            if gram_weight is None or gram_weight <= 0:
                continue

            amount = cls._to_float(portion.get("amount"), default=1.0) or 1.0
            if amount <= 0:
                amount = 1.0

            measure_unit = portion.get("measureUnit")
            measure_name = ""
            if isinstance(measure_unit, dict):
                measure_name = str(measure_unit.get("name", "")).strip().lower()

            modifier = str(portion.get("modifier", "")).strip().lower()
            combined_text = f"{measure_name} {modifier}".strip()

            grams_per_unit = gram_weight / amount

            if normalized_unit == "serving" and amount == 1:
                return PortionResolution(grams_per_unit, "usda", cls.USDA_CONFIDENCE, cls._detect_category(normalized_name))

            if cls._matches_unit_token(combined_text, normalized_unit):
                return PortionResolution(grams_per_unit, "usda", cls.USDA_CONFIDENCE, cls._detect_category(normalized_name))

        return None

    @classmethod
    def _resolve_from_fatsecret(cls, normalized_name: str, normalized_unit: str) -> PortionResolution | None:
        if not settings.FATSECRET_CLIENT_ID or not settings.FATSECRET_CLIENT_SECRET:
            return None

        access_token = cls._get_fatsecret_access_token()
        if not access_token:
            return None

        try:
            search_response = httpx.get(
                FATSECRET_API_URL,
                params={
                    "method": "foods.search.v3",
                    "search_expression": normalized_name,
                    "format": "json",
                },
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=cls.REQUEST_TIMEOUT_SECONDS,
            )
            search_response.raise_for_status()
        except httpx.HTTPError:
            return None

        search_data = search_response.json()
        foods_node = search_data.get("foods", {}) if isinstance(search_data, dict) else {}
        foods = foods_node.get("food", []) if isinstance(foods_node, dict) else []
        if isinstance(foods, dict):
            foods = [foods]
        if not isinstance(foods, list) or not foods:
            return None

        ranked_foods = sorted(
            [food for food in foods if isinstance(food, dict)],
            key=lambda item: fuzz.partial_token_set_ratio(normalized_name, str(item.get("food_name", ""))),
            reverse=True,
        )[:3]

        for food in ranked_foods:
            food_id = str(food.get("food_id", "")).strip()
            if not food_id:
                continue

            detail_resolution = cls._resolve_fatsecret_food_detail(access_token, food_id, normalized_name, normalized_unit)
            if detail_resolution is not None:
                return detail_resolution

        return None

    @classmethod
    def _resolve_fatsecret_food_detail(
        cls,
        access_token: str,
        food_id: str,
        normalized_name: str,
        normalized_unit: str,
    ) -> PortionResolution | None:
        try:
            detail_response = httpx.get(
                FATSECRET_API_URL,
                params={
                    "method": "food.get.v4",
                    "food_id": food_id,
                    "format": "json",
                },
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=cls.REQUEST_TIMEOUT_SECONDS,
            )
            detail_response.raise_for_status()
        except httpx.HTTPError:
            return None

        detail_data = detail_response.json()
        food_node = detail_data.get("food", {}) if isinstance(detail_data, dict) else {}
        servings_node = food_node.get("servings", {}) if isinstance(food_node, dict) else {}
        servings = servings_node.get("serving", []) if isinstance(servings_node, dict) else []
        if isinstance(servings, dict):
            servings = [servings]
        if not isinstance(servings, list):
            return None

        for serving in servings:
            if not isinstance(serving, dict):
                continue

            metric_amount = cls._to_float(serving.get("metric_serving_amount"))
            metric_unit = str(serving.get("metric_serving_unit", "")).strip().lower()
            serving_description = str(serving.get("serving_description", "")).strip().lower()

            grams_value = None
            if metric_amount and metric_amount > 0:
                if metric_unit in {"g", "gram", "grams"}:
                    grams_value = metric_amount
                elif metric_unit in {"ml", "milliliter", "milliliters"}:
                    grams_value = metric_amount

            if grams_value is None:
                continue

            if normalized_unit == "serving":
                return PortionResolution(grams_value, "fatsecret", cls.FATSECRET_CONFIDENCE, cls._detect_category(normalized_name))

            if cls._matches_unit_token(serving_description, normalized_unit):
                return PortionResolution(grams_value, "fatsecret", cls.FATSECRET_CONFIDENCE, cls._detect_category(normalized_name))

        return None

    @classmethod
    def _resolve_from_openfoodfacts(cls, normalized_name: str, normalized_unit: str) -> PortionResolution | None:
        try:
            response = httpx.get(
                OPENFOODFACTS_SEARCH_URL,
                params={
                    "search_terms": normalized_name,
                    "search_simple": "1",
                    "action": "process",
                    "json": "1",
                    "page_size": "10",
                },
                headers={"User-Agent": settings.OPENFOODFACTS_USER_AGENT},
                timeout=cls.REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
        except httpx.HTTPError:
            return None

        data = response.json()
        products = data.get("products", []) if isinstance(data, dict) else []
        if not isinstance(products, list) or not products:
            return None

        ranked_products = sorted(
            [product for product in products if isinstance(product, dict)],
            key=lambda item: fuzz.partial_token_set_ratio(
                normalized_name,
                str(item.get("product_name_en") or item.get("product_name") or ""),
            ),
            reverse=True,
        )[:3]

        for product in ranked_products:
            resolution = cls._extract_off_resolution(product, normalized_name, normalized_unit)
            if resolution is not None:
                return resolution

        return None

    @classmethod
    def _extract_off_resolution(
        cls,
        product: dict[str, Any],
        normalized_name: str,
        normalized_unit: str,
    ) -> PortionResolution | None:
        serving_quantity = cls._to_float(product.get("serving_quantity"))
        serving_unit = str(product.get("serving_quantity_unit", "")).strip().lower()
        serving_size_text = str(product.get("serving_size", "")).strip().lower()

        grams_from_text = cls._extract_grams_from_text(serving_size_text)
        if grams_from_text is None and serving_quantity and serving_unit in {"g", "gram", "grams"}:
            grams_from_text = serving_quantity
        elif grams_from_text is None and serving_quantity and serving_unit in {"ml", "milliliter", "milliliters"}:
            grams_from_text = serving_quantity

        if grams_from_text is None:
            return None

        if normalized_unit == "serving":
            return PortionResolution(grams_from_text, "openfoodfacts", cls.OPENFOODFACTS_CONFIDENCE, cls._detect_category(normalized_name))

        if cls._matches_unit_token(serving_size_text, normalized_unit):
            return PortionResolution(grams_from_text, "openfoodfacts", cls.OPENFOODFACTS_CONFIDENCE, cls._detect_category(normalized_name))

        return None

    @classmethod
    def _get_fatsecret_access_token(cls) -> str | None:
        try:
            response = httpx.post(
                FATSECRET_OAUTH_URL,
                auth=(settings.FATSECRET_CLIENT_ID, settings.FATSECRET_CLIENT_SECRET),
                data={"grant_type": "client_credentials", "scope": "basic"},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=cls.REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
        except httpx.HTTPError:
            return None

        data = response.json()
        token = data.get("access_token") if isinstance(data, dict) else None
        if token is None:
            return None

        token_str = str(token).strip()
        return token_str or None

    @classmethod
    def _extract_grams_from_text(cls, text: str) -> float | None:
        if not text:
            return None

        match = re.search(r"([0-9]+(?:[\.,][0-9]+)?)\s*g\b", text, flags=re.IGNORECASE)
        if not match:
            return None

        value = match.group(1).replace(",", ".")
        return cls._to_float(value)

    @classmethod
    def _category_fallback_grams(cls, category: str, normalized_unit: str) -> float:
        category_table = cls.CATEGORY_FALLBACK_GRAMS.get(category, cls.CATEGORY_FALLBACK_GRAMS["generic"])
        return category_table.get(normalized_unit, cls.CATEGORY_FALLBACK_GRAMS["generic"].get(normalized_unit, 100.0))

    @classmethod
    def _detect_category(cls, normalized_name: str) -> str:
        for category, keywords in cls.CATEGORY_KEYWORDS.items():
            if any(keyword in normalized_name for keyword in keywords):
                return category
        return "generic"

    @classmethod
    def _matches_unit_token(cls, text: str, normalized_unit: str) -> bool:
        tokens = cls.UNIT_TOKEN_MATCH.get(normalized_unit, {normalized_unit})
        return any(token in text for token in tokens)

    @staticmethod
    def _to_float(value: Any, default: float | None = None) -> float | None:
        if value is None:
            return default
        try:
            return float(value)
        except (TypeError, ValueError):
            return default
