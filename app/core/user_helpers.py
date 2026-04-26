from __future__ import annotations
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.db.models import User


def get_current_user_id(user: "User") -> int:
    """Extract integer user ID from a User model instance."""
    return int(getattr(user, "id"))


def extract_weight_kg(user: "User", fallback: float = 0.0) -> float:
    """Extract user weight_kg as float, returning fallback if missing or falsy."""
    return float(getattr(user, "weight_kg", fallback) or fallback)


def extract_user_bio(user: "User", fields: list[str]) -> dict[str, Any]:
    """Extract user biographical data as a dict using getattr with None defaults."""
    return {field: getattr(user, field, None) for field in fields}
