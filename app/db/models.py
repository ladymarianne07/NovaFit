from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON, Boolean, Float
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
from ..constants import DatabaseConstants


Base = declarative_base()


class User(Base):
    """User model with authentication support"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(DatabaseConstants.MAX_STRING_LENGTH), unique=True, index=True, nullable=False)
    hashed_password = Column(String(DatabaseConstants.MAX_STRING_LENGTH), nullable=False)
    
    # Profile fields (required)
    first_name = Column(String(DatabaseConstants.MAX_NAME_LENGTH), nullable=False)
    last_name = Column(String(DatabaseConstants.MAX_NAME_LENGTH), nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Biometric data for caloric calculations (required for full registration)
    age = Column(Integer, nullable=False)
    gender = Column(String(10), nullable=False)  # 'male' or 'female'
    weight = Column(Float, nullable=False)  # in kg
    height = Column(Float, nullable=False)  # in cm
    activity_level = Column(Float, nullable=False)  # activity factor (1.20-1.80)
    
    # Calculated values (automatically computed when biometric data changes)
    bmr = Column(Float, nullable=False)  # Basal Metabolic Rate
    daily_caloric_expenditure = Column(Float, nullable=False)  # BMR * activity_level (TDEE)
    
    # Fitness objective and personalized targets
    objective = Column(String(50), nullable=True)  # 'maintenance', 'fat_loss', 'muscle_gain', 'body_recomp', 'performance'
    aggressiveness_level = Column(Integer, nullable=True)  # 1-3 for applicable objectives
    
    # Target values based on objective (automatically computed when objective or aggressiveness changes)
    target_calories = Column(Float, nullable=True)  # Target daily calories
    protein_target_g = Column(Float, nullable=True)  # Daily protein target in grams
    fat_target_g = Column(Float, nullable=True)  # Daily fat target in grams
    carbs_target_g = Column(Float, nullable=True)  # Daily carbs target in grams
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    events = relationship("Event", back_populates="user", cascade="all, delete-orphan")
    skinfold_measurements = relationship("SkinfoldMeasurement", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(email='{self.email}')>"


class Event(Base):
    """Event/Activity model for timeline tracking (append-only design)"""
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Event metadata
    event_type = Column(String(50), nullable=False, index=True)  # 'workout', 'meal', 'weight', etc.
    title = Column(String(DatabaseConstants.MAX_TITLE_LENGTH), nullable=False)
    description = Column(Text, nullable=True)
    
    # Flexible data payload (JSON field for extensibility)
    data = Column(JSON, nullable=True)  # e.g., {'duration': 45, 'calories': 300, 'exercises': [...]}
    
    # Timestamps (append-only: no updates after creation)
    event_timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Optional soft delete (instead of actual deletion for data integrity)
    is_deleted = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="events")
    
    def __repr__(self):
        return f"<Event(type='{self.event_type}', user_id={self.user_id})>"


class DailyNutrition(Base):
    """Daily nutrition tracking for macronutrients"""
    __tablename__ = "daily_nutrition"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Date for the nutrition tracking (one record per user per date)
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Macronutrients in grams
    carbs_consumed = Column(Float, default=0.0, nullable=False)  # in grams
    protein_consumed = Column(Float, default=0.0, nullable=False)  # in grams  
    fat_consumed = Column(Float, default=0.0, nullable=False)  # in grams
    
    # Daily targets in grams (calculated based on user profile)
    carbs_target = Column(Float, nullable=False)  # in grams
    protein_target = Column(Float, nullable=False)  # in grams
    fat_target = Column(Float, nullable=False)  # in grams
    
    # Total calories from macros
    total_calories = Column(Float, default=0.0, nullable=False)  # calculated field
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    
    def __repr__(self):
        return f"<DailyNutrition(user_id={self.user_id}, date={self.date})>"


class SkinfoldMeasurement(Base):
    """Stored skinfold measurements and computed body composition values."""
    __tablename__ = "skinfold_measurements"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    method = Column(String(100), nullable=False)
    measurement_unit = Column(String(10), nullable=False, default="mm")
    measured_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    sex = Column(String(10), nullable=False)
    age_years = Column(Integer, nullable=False)
    weight_kg = Column(Float, nullable=True)

    chest_mm = Column(Float, nullable=True)
    midaxillary_mm = Column(Float, nullable=True)
    triceps_mm = Column(Float, nullable=True)
    subscapular_mm = Column(Float, nullable=True)
    abdomen_mm = Column(Float, nullable=True)
    suprailiac_mm = Column(Float, nullable=True)
    thigh_mm = Column(Float, nullable=True)

    sum_of_skinfolds_mm = Column(Float, nullable=False)
    body_density = Column(Float, nullable=False)
    body_fat_percent = Column(Float, nullable=False)
    fat_free_mass_percent = Column(Float, nullable=False)
    fat_mass_kg = Column(Float, nullable=True)
    lean_mass_kg = Column(Float, nullable=True)
    warnings = Column(JSON, nullable=False, default=list)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="skinfold_measurements")

    def __repr__(self):
        return f"<SkinfoldMeasurement(user_id={self.user_id}, method='{self.method}')>"


# Database indexes for performance
# These will be created automatically by SQLAlchemy when tables are created
# Index on (user_id, event_timestamp) for efficient user timeline queries
# Index on (user_id, event_type) for filtering by event type
# Index on (event_timestamp) for global timeline queries (if needed later)