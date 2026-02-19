from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence

from ...schemas.food_normalized import FoodNormalized


class FoodConnector(ABC):
    """Abstract connector contract for external food providers."""

    source_name: str

    @abstractmethod
    async def search(self, query: str) -> list[FoodNormalized]:
        """Search provider and return normalized food results."""
        raise NotImplementedError


def clamp_confidence(value: float) -> float:
    """Clamp confidence score to [0.0, 1.0]."""
    return max(0.0, min(1.0, round(value, 4)))


def first_non_empty(values: Sequence[object]) -> str | None:
    """Return first non-empty string representation from a sequence."""
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return None
