from __future__ import annotations

import asyncio
import logging
import re
import time
from dataclasses import dataclass

from rapidfuzz import fuzz
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models.food import FoodEntry
from ..schemas.food_normalized import FoodNormalized
from .connectors import FatSecretConnector, FoodConnector, OpenFoodFactsConnector, USDAConnector
from .connectors.base_connector import clamp_confidence


logger = logging.getLogger(__name__)

BARCODE_PATTERN = re.compile(r"^\d{9,}$")
KNOWN_BRAND_TOKENS = {
    "coca",
    "coca-cola",
    "pepsi",
    "nestle",
    "danone",
    "kellogg",
    "bimbo",
    "lays",
    "lay's",
    "gatorade",
    "monster",
    "redbull",
}

MAX_RESULTS = 5


@dataclass
class ConnectorTimedResult:
    source: str
    elapsed_ms: float
    items: list[FoodNormalized]


class FoodAggregatorService:
    """Aggregate food search across multiple providers and return ranked normalized results."""

    def __init__(self, connectors: list[FoodConnector] | None = None) -> None:
        self.connectors = connectors or [
            USDAConnector(),
            OpenFoodFactsConnector(),
            FatSecretConnector(),
        ]

    async def search_food(self, query: str, db: Session | None = None) -> list[FoodNormalized]:
        """Search all providers in parallel and return top ranked normalized foods."""
        cleaned_query = query.strip()
        if not cleaned_query:
            return []

        start = time.perf_counter()

        # TODO: integrate Redis cache

        tasks = [self._run_connector(connector=connector, query=cleaned_query) for connector in self.connectors]
        connector_runs = await asyncio.gather(*tasks, return_exceptions=False)

        results_by_source = {
            run.source: run.items
            for run in connector_runs
        }

        combined: list[FoodNormalized] = []
        for run in connector_runs:
            logger.info(
                "food_aggregation_source_result source=%s elapsed_ms=%.2f result_count=%d query=%s",
                run.source,
                run.elapsed_ms,
                len(run.items),
                cleaned_query,
            )
            combined.extend(run.items)

        ranked = self._apply_ranking_rules(
            query=cleaned_query,
            items=combined,
            db=db,
            results_by_source=results_by_source,
        )

        total_elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "food_aggregation_completed elapsed_ms=%.2f total_results=%d top_results=%d query=%s",
            total_elapsed_ms,
            len(combined),
            len(ranked),
            cleaned_query,
        )

        return ranked

    async def _run_connector(self, connector: FoodConnector, query: str) -> ConnectorTimedResult:
        started = time.perf_counter()
        items = await connector.search(query)
        elapsed_ms = (time.perf_counter() - started) * 1000
        return ConnectorTimedResult(source=connector.source_name, elapsed_ms=elapsed_ms, items=items)

    def _apply_ranking_rules(
        self,
        query: str,
        items: list[FoodNormalized],
        db: Session | None,
        results_by_source: dict[str, list[FoodNormalized]],
    ) -> list[FoodNormalized]:
        if not items:
            return []

        is_barcode_query = bool(BARCODE_PATTERN.fullmatch(query))
        has_brand_in_query = _query_has_brand(query)
        exists_in_local_db = _exists_in_local_db(query=query, db=db)

        rescored: list[FoodNormalized] = []
        for item in items:
            score = item.confidence_score

            if is_barcode_query:
                if item.source == "openfoodfacts":
                    score += 0.10
                else:
                    score -= 0.04

            if not has_brand_in_query:
                if item.source == "usda":
                    score += 0.08
                elif item.source == "openfoodfacts":
                    score -= 0.03

            if exists_in_local_db and _is_query_similar_to_item(query, item):
                score += 0.05

            if item.fiber_per_100g is None:
                score -= 0.05

            if (
                item.protein_per_100g == 0
                and item.fat_per_100g == 0
                and item.carbs_per_100g == 0
            ):
                score -= 0.05

            rescored.append(item.model_copy(update={"confidence_score": clamp_confidence(score)}))

        deduplicated = self._remove_duplicates(rescored)
        deduplicated.sort(key=lambda x: x.confidence_score, reverse=True)

        # If barcode query and OFF returned results, ensure OFF appears first.
        if is_barcode_query and results_by_source.get("openfoodfacts"):
            deduplicated.sort(
                key=lambda x: (x.source != "openfoodfacts", -x.confidence_score)
            )

        return deduplicated[:MAX_RESULTS]

    def _remove_duplicates(self, items: list[FoodNormalized]) -> list[FoodNormalized]:
        sorted_items = sorted(items, key=lambda x: x.confidence_score, reverse=True)

        unique: list[FoodNormalized] = []
        for candidate in sorted_items:
            if any(_is_duplicate_food(candidate, existing) for existing in unique):
                continue
            unique.append(candidate)

        return unique


def _query_has_brand(query: str) -> bool:
    lowered = query.lower().strip()

    if BARCODE_PATTERN.fullmatch(lowered):
        return True

    tokens = re.findall(r"[a-z0-9'\-]+", lowered)
    if any(token in KNOWN_BRAND_TOKENS for token in tokens):
        return True

    # Heuristic: alphanumeric product references are likely branded.
    return any(any(ch.isdigit() for ch in token) and any(ch.isalpha() for ch in token) for token in tokens)


def _exists_in_local_db(query: str, db: Session | None) -> bool:
    if db is None:
        return False

    lowered_query = query.strip().lower()
    if not lowered_query:
        return False

    count = (
        db.query(FoodEntry)
        .filter(func.lower(FoodEntry.normalized_name).like(f"%{lowered_query}%"))
        .count()
    )

    return count > 0


def _is_query_similar_to_item(query: str, item: FoodNormalized) -> bool:
    target = f"{item.name} {item.brand or ''}".strip().lower()
    return fuzz.token_set_ratio(query.lower().strip(), target) >= 70


def _is_duplicate_food(left: FoodNormalized, right: FoodNormalized) -> bool:
    left_key = f"{left.name} {left.brand or ''}".strip().lower()
    right_key = f"{right.name} {right.brand or ''}".strip().lower()

    return fuzz.token_set_ratio(left_key, right_key) >= 92


async def search_food(query: str, db: Session | None = None) -> list[FoodNormalized]:
    """Convenience async function ready to be plugged into a FastAPI router."""
    service = FoodAggregatorService()
    return await service.search_food(query=query, db=db)
