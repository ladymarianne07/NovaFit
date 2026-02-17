from sqlalchemy import Column, DateTime, Float, Integer, String
from sqlalchemy.sql import func

from ..constants import DatabaseConstants
from ..db.models import Base


class FoodEntry(Base):
    """Food entry persisted after parsing and calorie calculation."""

    __tablename__ = "food_entries"

    id = Column(Integer, primary_key=True, index=True)
    original_text = Column(String(DatabaseConstants.MAX_STRING_LENGTH), nullable=False)
    normalized_name = Column(String(DatabaseConstants.MAX_TITLE_LENGTH), nullable=False, index=True)
    quantity_grams = Column(Float, nullable=False)
    usda_fdc_id = Column(String(50), nullable=False)
    calories_per_100g = Column(Float, nullable=False)
    total_calories = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<FoodEntry(id={self.id}, normalized_name='{self.normalized_name}')>"
