from sqlalchemy import Column, DateTime, Float, Integer, String
from sqlalchemy.sql import func

from ..db.models import Base


class FoodPortionCache(Base):
    """Persistent cache of resolved grams-per-unit by food name and unit."""

    __tablename__ = "food_portion_cache"

    id = Column(Integer, primary_key=True, index=True)
    normalized_name = Column(String(255), nullable=False, index=True)
    unit_normalized = Column(String(50), nullable=False, index=True)
    grams_per_unit = Column(Float, nullable=False)
    source = Column(String(50), nullable=False)
    confidence_score = Column(Float, nullable=False, default=0.0)
    category = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self) -> str:
        return (
            f"<FoodPortionCache(name='{self.normalized_name}', unit='{self.unit_normalized}', "
            f"grams_per_unit={self.grams_per_unit})>"
        )
