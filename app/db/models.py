from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Date, Text, ForeignKey, JSON, Boolean, Float
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
    role = Column(String(20), nullable=False, default="student")  # 'student' | 'trainer'
    
    # Trainer preference: does this trainer also use the app for themselves?
    uses_app_for_self = Column(Boolean, nullable=True, default=None)

    # Biometric data for caloric calculations (required for students; optional for trainers who don't use the app for themselves)
    age = Column(Integer, nullable=True)
    gender = Column(String(10), nullable=True)  # 'male' or 'female'
    weight_kg = Column(Float, nullable=True)  # in kg
    height_cm = Column(Float, nullable=True)  # in cm
    activity_level = Column(Float, nullable=True)  # activity factor (1.20-1.80)

    # Calculated values (automatically computed when biometric data changes; null for trainers without self-use)
    bmr_bpm = Column(Float, nullable=True)  # Basal Metabolic Rate
    daily_caloric_expenditure = Column(Float, nullable=True)  # BMR * activity_level (TDEE)
    
    # Fitness objective and personalized targets
    objective = Column(String(50), nullable=True)  # 'maintenance', 'fat_loss', 'muscle_gain', 'body_recomp', 'performance'
    aggressiveness_level = Column(Integer, nullable=True)  # 1-3 for applicable objectives
    
    # Target values based on objective (automatically computed when objective or aggressiveness changes)
    target_calories = Column(Float, nullable=True)  # Target daily calories
    protein_target_g = Column(Float, nullable=True)  # Daily protein target in grams
    fat_target_g = Column(Float, nullable=True)  # Daily fat target in grams
    carbs_target_g = Column(Float, nullable=True)  # Daily carbs target in grams

    # Optional user-overridden nutrition planning values
    custom_target_calories = Column(Float, nullable=True)  # Manual daily calories goal
    carbs_target_percent = Column(Float, nullable=True)  # % calories from carbs
    protein_target_percent = Column(Float, nullable=True)  # % calories from protein
    fat_target_percent = Column(Float, nullable=True)  # % calories from fat
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    events = relationship("Event", back_populates="user", cascade="all, delete-orphan")
    skinfold_measurements = relationship("SkinfoldMeasurement", back_populates="user", cascade="all, delete-orphan")
    workout_sessions = relationship("WorkoutSession", back_populates="user", cascade="all, delete-orphan")
    workout_correction_factors = relationship("WorkoutCorrectionFactor", back_populates="user", cascade="all, delete-orphan")
    exercise_daily_energy_logs = relationship("ExerciseDailyEnergyLog", back_populates="user", cascade="all, delete-orphan")
    routine = relationship("UserRoutine", back_populates="user", uselist=False, cascade="all, delete-orphan")
    diet = relationship("UserDiet", back_populates="user", uselist=False, cascade="all, delete-orphan")
    trainer_links = relationship("TrainerStudent", foreign_keys="[TrainerStudent.trainer_id]", back_populates="trainer", cascade="all, delete-orphan")
    student_links = relationship("TrainerStudent", foreign_keys="[TrainerStudent.student_id]", back_populates="student", cascade="all, delete-orphan")
    received_notifications = relationship("Notification", foreign_keys="[Notification.recipient_id]", back_populates="recipient", cascade="all, delete-orphan")
    sent_notifications = relationship("Notification", foreign_keys="[Notification.sender_id]", back_populates="sender")
    trainer_invites = relationship("TrainerInvite", foreign_keys="[TrainerInvite.trainer_id]", back_populates="trainer", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(email='{self.email}')>"

    @property
    def weight(self) -> float | None:
        return self.weight_kg

    @property
    def height(self) -> float | None:
        return self.height_cm

    @property
    def bmr(self) -> float | None:
        return self.bmr_bpm


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


class ExerciseActivity(Base):
    """MET activity catalog for exercise calorie calculations."""

    __tablename__ = "exercise_activities"

    id = Column(Integer, primary_key=True, index=True)
    activity_key = Column(String(100), unique=True, nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)
    label_es = Column(String(150), nullable=False)

    met_low = Column(Float, nullable=False)
    met_medium = Column(Float, nullable=False)
    met_high = Column(Float, nullable=False)

    source_refs = Column(JSON, nullable=False, default=dict)
    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    workout_blocks = relationship("WorkoutSessionBlock", back_populates="activity")

    def __repr__(self):
        return f"<ExerciseActivity(activity_key='{self.activity_key}', category='{self.category}')>"


class WorkoutSession(Base):
    """Persisted workout session, usually generated from free-text AI parsing."""

    __tablename__ = "workout_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    session_date = Column(Date, nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)

    source = Column(String(20), nullable=False, default="ai")
    status = Column(String(20), nullable=False, default="draft")

    raw_input = Column(Text, nullable=True)
    ai_output = Column(JSON, nullable=True)

    total_kcal_min = Column(Float, nullable=True)
    total_kcal_max = Column(Float, nullable=True)
    total_kcal_est = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="workout_sessions")
    blocks = relationship("WorkoutSessionBlock", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<WorkoutSession(user_id={self.user_id}, date={self.session_date})>"


class WorkoutSessionBlock(Base):
    """Workout activity block within a session."""

    __tablename__ = "workout_session_blocks"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("workout_sessions.id"), nullable=False, index=True)
    activity_id = Column(Integer, ForeignKey("exercise_activities.id"), nullable=False, index=True)

    block_order = Column(Integer, nullable=False)
    duration_minutes = Column(Integer, nullable=False)

    intensity_level = Column(String(20), nullable=True)
    intensity_raw = Column(String(120), nullable=True)

    weight_kg_used = Column(Float, nullable=True)

    met_used_min = Column(Float, nullable=True)
    met_used_max = Column(Float, nullable=True)

    correction_factor = Column(Float, nullable=False, default=1.0)

    kcal_min = Column(Float, nullable=True)
    kcal_max = Column(Float, nullable=True)
    kcal_est = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("WorkoutSession", back_populates="blocks")
    activity = relationship("ExerciseActivity", back_populates="workout_blocks")

    def __repr__(self):
        return f"<WorkoutSessionBlock(session_id={self.session_id}, order={self.block_order})>"


class WorkoutCorrectionFactor(Base):
    """User-specific correction factors to calibrate MET estimations."""

    __tablename__ = "workout_correction_factors"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    scope = Column(String(20), nullable=False, default="global")
    category = Column(String(100), nullable=True)
    activity_key = Column(String(100), nullable=True)

    factor = Column(Float, nullable=False, default=1.0)
    method = Column(String(30), nullable=False, default="manual")

    effective_from = Column(Date, nullable=False, default=lambda: datetime.now(timezone.utc).date())
    effective_to = Column(Date, nullable=True)

    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="workout_correction_factors")

    def __repr__(self):
        return f"<WorkoutCorrectionFactor(user_id={self.user_id}, scope='{self.scope}', factor={self.factor})>"


class ExerciseDailyEnergyLog(Base):
    """Daily exercise energy aggregates for dashboard usage."""

    __tablename__ = "exercise_daily_energy_log"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    log_date = Column(Date, nullable=False, index=True)

    exercise_kcal_min = Column(Float, nullable=False, default=0.0)
    exercise_kcal_max = Column(Float, nullable=False, default=0.0)
    exercise_kcal_est = Column(Float, nullable=False, default=0.0)

    intake_kcal = Column(Float, nullable=False, default=0.0)
    net_kcal_est = Column(Float, nullable=False, default=0.0)

    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="exercise_daily_energy_logs")

    def __repr__(self):
        return f"<ExerciseDailyEnergyLog(user_id={self.user_id}, date={self.log_date})>"


class UserRoutine(Base):
    """User's active workout routine — uploaded from file or generated by AI."""

    __tablename__ = "user_routines"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)

    source_filename = Column(String(DatabaseConstants.MAX_STRING_LENGTH), nullable=True)
    source_type = Column(String(20), nullable=True, default="file")  # 'file' | 'ai_text'
    status = Column(String(20), nullable=False, default="processing")  # processing | ready | error

    # Gemini-generated HTML (self-contained, inline CSS/JS with 3-theme switcher)
    html_content = Column(Text, nullable=True)

    # Structured JSON: sessions + exercises + estimated calories
    routine_data = Column(JSON, nullable=True)

    # PT analysis: conditions detected, contraindications applied, adaptations, warnings
    health_analysis = Column(JSON, nullable=True)

    # Stored intake form data (used for re-edit requests)
    intake_data = Column(JSON, nullable=True)

    error_message = Column(Text, nullable=True)

    # Sequential progression — index of the next session to do (wraps around)
    current_session_index = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="routine")

    def __repr__(self):
        return f"<UserRoutine(user_id={self.user_id}, status='{self.status}', source='{self.source_type}')>"


class UserDiet(Base):
    """User's active diet plan — AI generated based on profile macros and routine data."""

    __tablename__ = "user_diets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)

    source_type = Column(String(20), nullable=True, default="ai_text")
    status = Column(String(20), nullable=False, default="processing")  # processing | ready | error

    # Gemini-generated HTML (self-contained, inline CSS with 3-theme switcher)
    html_content = Column(Text, nullable=True)

    # Structured JSON: training_day meals, rest_day meals, macros, water intake
    diet_data = Column(JSON, nullable=True)

    # Stored intake form data (used for re-edit requests)
    intake_data = Column(JSON, nullable=True)

    error_message = Column(Text, nullable=True)

    # Meal tracker state (resets daily — like current_session_index on UserRoutine)
    current_meal_index = Column(Integer, nullable=False, default=0)
    current_meal_date = Column(Date, nullable=True)  # NULL = never tracked yet

    # Daily macro tracking — {"2026-04-02": {"calories": 304.0, "protein_g": 20.0, "carbs_g": 37.0, "fat_g": 9.0}}
    daily_consumed = Column(JSON, nullable=True)

    # Per-day meal overrides (expires automatically at midnight) — {"2026-04-02": {"0": {...meal_dict}}}
    daily_overrides = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="diet")

    def __repr__(self):
        return f"<UserDiet(user_id={self.user_id}, status='{self.status}')>"


class TrainerStudent(Base):
    """Relationship between a trainer and their students."""
    __tablename__ = "trainer_students"

    id = Column(Integer, primary_key=True, index=True)
    trainer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="active")  # 'active' | 'revoked'

    linked_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    trainer = relationship("User", foreign_keys=[trainer_id], back_populates="trainer_links")
    student = relationship("User", foreign_keys=[student_id], back_populates="student_links")

    def __repr__(self):
        return f"<TrainerStudent(trainer_id={self.trainer_id}, student_id={self.student_id}, status='{self.status}')>"


class TrainerInvite(Base):
    """Invite codes generated by trainers for students to link accounts."""
    __tablename__ = "trainer_invites"

    id = Column(Integer, primary_key=True, index=True)
    trainer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    used_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    trainer = relationship("User", foreign_keys=[trainer_id], back_populates="trainer_invites")

    def __repr__(self):
        return f"<TrainerInvite(trainer_id={self.trainer_id}, code='{self.code}')>"


class Notification(Base):
    """In-app notifications between trainers and students."""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    type = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    body = Column(String(500), nullable=False)
    data = Column(JSON, nullable=True)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    recipient = relationship("User", foreign_keys=[recipient_id], back_populates="received_notifications")
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_notifications")

    def __repr__(self):
        return f"<Notification(recipient_id={self.recipient_id}, type='{self.type}', is_read={self.is_read})>"


# Database indexes for performance
# These will be created automatically by SQLAlchemy when tables are created
# Index on (user_id, event_timestamp) for efficient user timeline queries
# Index on (user_id, event_type) for filtering by event type
# Index on (event_timestamp) for global timeline queries (if needed later)