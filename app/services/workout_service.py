"""Workout Service - MET based calculations and workout persistence helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, cast

from sqlalchemy.orm import Session

from ..constants import WorkoutConstants
from ..core.custom_exceptions import (
    WorkoutActivityNotFoundError,
    WorkoutValidationError,
    WorkoutWeightRequiredError,
)
from ..db.models import (
    ExerciseActivity,
    ExerciseDailyEnergyLog,
    WorkoutCorrectionFactor,
    WorkoutSession,
    WorkoutSessionBlock,
)


@dataclass(slots=True)
class WorkoutBlockMetrics:
    """Normalized MET and kcal metrics for a workout block."""

    intensity_level: str
    met_used_min: float
    met_used_max: float
    correction_factor: float
    kcal_min: float
    kcal_max: float
    kcal_est: float


class WorkoutService:
    """Business logic for workout MET-based calorie calculations."""

    _INTENSITY_ALIASES: dict[str, str] = {
        "baja": WorkoutConstants.INTENSITY_LOW,
        "suave": WorkoutConstants.INTENSITY_LOW,
        "ligera": WorkoutConstants.INTENSITY_LOW,
        "light": WorkoutConstants.INTENSITY_LOW,
        "low": WorkoutConstants.INTENSITY_LOW,
        "media": WorkoutConstants.INTENSITY_MEDIUM,
        "moderada": WorkoutConstants.INTENSITY_MEDIUM,
        "medium": WorkoutConstants.INTENSITY_MEDIUM,
        "moderate": WorkoutConstants.INTENSITY_MEDIUM,
        "alta": WorkoutConstants.INTENSITY_HIGH,
        "intensa": WorkoutConstants.INTENSITY_HIGH,
        "high": WorkoutConstants.INTENSITY_HIGH,
        "hard": WorkoutConstants.INTENSITY_HIGH,
        "vigorous": WorkoutConstants.INTENSITY_HIGH,
    }

    @classmethod
    def normalize_intensity(cls, value: str | None) -> str:
        """Normalize free-text intensity to low/medium/high."""
        if not value:
            return WorkoutConstants.DEFAULT_INTENSITY_ESTIMATE

        normalized_value = value.strip().lower()
        if normalized_value in WorkoutConstants.VALID_INTENSITY_LEVELS:
            return normalized_value

        return cls._INTENSITY_ALIASES.get(
            normalized_value,
            WorkoutConstants.DEFAULT_INTENSITY_ESTIMATE,
        )

    @classmethod
    def validate_session_source(cls, source: str) -> str:
        """Validate and normalize session source."""
        normalized_source = source.strip().lower()
        if normalized_source not in WorkoutConstants.VALID_SOURCES:
            raise WorkoutValidationError(
                f"Invalid workout source '{source}'. Valid: {sorted(WorkoutConstants.VALID_SOURCES)}"
            )
        return normalized_source

    @classmethod
    def resolve_activity(cls, db: Session, activity_query: str) -> ExerciseActivity:
        """Resolve activity by key (preferred) or exact label match."""
        query = activity_query.strip().lower()
        activity = (
            db.query(ExerciseActivity)
            .filter(ExerciseActivity.activity_key == query, ExerciseActivity.is_active == True)  # noqa: E712
            .first()
        )
        if activity:
            return activity

        activity = (
            db.query(ExerciseActivity)
            .filter(ExerciseActivity.label_es.ilike(activity_query.strip()), ExerciseActivity.is_active == True)  # noqa: E712
            .first()
        )
        if activity:
            return activity

        raise WorkoutActivityNotFoundError(
            f"Could not resolve workout activity '{activity_query}'"
        )

    @classmethod
    def get_effective_correction_factor(
        cls,
        db: Session,
        user_id: int,
        session_date: date,
        activity: ExerciseActivity,
    ) -> float:
        """Resolve most specific active correction factor for a user/date."""
        base_query = db.query(WorkoutCorrectionFactor).filter(
            WorkoutCorrectionFactor.user_id == user_id,
            WorkoutCorrectionFactor.effective_from <= session_date,
        )

        matching_rows = [
            factor
            for factor in base_query.all()
            if (
                getattr(cast(Any, factor), "effective_to", None) is None
                or getattr(cast(Any, factor), "effective_to") >= session_date
            )
        ]

        if not matching_rows:
            return WorkoutConstants.DEFAULT_CORRECTION_FACTOR

        def _priority(factor: WorkoutCorrectionFactor) -> int:
            scope = getattr(cast(Any, factor), "scope", "")
            activity_key = getattr(cast(Any, factor), "activity_key", None)
            category = getattr(cast(Any, factor), "category", None)
            if scope == "activity_key" and activity_key == getattr(cast(Any, activity), "activity_key", None):
                return 3
            if scope == "category" and category == getattr(cast(Any, activity), "category", None):
                return 2
            if scope == "global":
                return 1
            return 0

        sorted_rows = sorted(
            matching_rows,
            key=lambda factor: (
                _priority(factor),
                getattr(cast(Any, factor), "updated_at", None) is not None,
                getattr(cast(Any, factor), "updated_at", None),
                getattr(cast(Any, factor), "id", 0),
            ),
            reverse=True,
        )

        best = sorted_rows[0]
        return cls._clamp_correction_factor(float(getattr(cast(Any, best), "factor", 1.0)))

    @classmethod
    def calculate_block_metrics(
        cls,
        *,
        activity: ExerciseActivity,
        duration_minutes: int,
        weight_kg: float | None,
        intensity_level: str | None,
        correction_factor: float,
    ) -> WorkoutBlockMetrics:
        """Calculate MET window and kcal values for one workout block."""
        cls._validate_duration(duration_minutes)

        if weight_kg is None or weight_kg <= 0:
            raise WorkoutWeightRequiredError(
                "User weight is required to calculate workout calories"
            )

        normalized_intensity = cls.normalize_intensity(intensity_level)
        met_min, met_max = cls._resolve_met_window(activity, normalized_intensity)
        factor = cls._clamp_correction_factor(correction_factor)

        corrected_met_min = met_min * factor
        corrected_met_max = met_max * factor
        met_est = (corrected_met_min + corrected_met_max) / 2.0
        hours = duration_minutes / 60.0

        kcal_min = corrected_met_min * float(weight_kg) * hours
        kcal_max = corrected_met_max * float(weight_kg) * hours
        kcal_est = met_est * float(weight_kg) * hours

        return WorkoutBlockMetrics(
            intensity_level=normalized_intensity,
            met_used_min=round(corrected_met_min, 3),
            met_used_max=round(corrected_met_max, 3),
            correction_factor=factor,
            kcal_min=round(kcal_min, 2),
            kcal_max=round(kcal_max, 2),
            kcal_est=round(kcal_est, 2),
        )

    @classmethod
    def recalculate_session_totals(cls, session: WorkoutSession) -> tuple[float, float, float]:
        """Aggregate totals from all session blocks and persist in entity."""
        session_data = cast(Any, session)
        blocks: list[Any] = list(getattr(session_data, "blocks", []) or [])
        total_min = round(sum(float(getattr(block, "kcal_min", 0.0) or 0.0) for block in blocks), 2)
        total_max = round(sum(float(getattr(block, "kcal_max", 0.0) or 0.0) for block in blocks), 2)
        total_est = round(sum(float(getattr(block, "kcal_est", 0.0) or 0.0) for block in blocks), 2)

        session_data.total_kcal_min = total_min
        session_data.total_kcal_max = total_max
        session_data.total_kcal_est = total_est
        return total_min, total_max, total_est

    @classmethod
    def upsert_daily_energy_log(
        cls,
        db: Session,
        *,
        user_id: int,
        log_date: date,
        exercise_kcal_min: float,
        exercise_kcal_max: float,
        exercise_kcal_est: float,
        intake_kcal: float | None = None,
    ) -> ExerciseDailyEnergyLog:
        """Create or update daily exercise totals used by dashboard."""
        log = (
            db.query(ExerciseDailyEnergyLog)
            .filter(
                ExerciseDailyEnergyLog.user_id == user_id,
                ExerciseDailyEnergyLog.log_date == log_date,
            )
            .first()
        )

        if log is None:
            log = ExerciseDailyEnergyLog(
                user_id=user_id,
                log_date=log_date,
            )
            db.add(log)

        log_data = cast(Any, log)

        log_data.exercise_kcal_min = round(max(0.0, float(exercise_kcal_min)), 2)
        log_data.exercise_kcal_max = round(max(0.0, float(exercise_kcal_max)), 2)
        log_data.exercise_kcal_est = round(max(0.0, float(exercise_kcal_est)), 2)

        if intake_kcal is not None:
            log_data.intake_kcal = round(max(0.0, float(intake_kcal)), 2)

        log_data.net_kcal_est = round(
            float(getattr(log_data, "intake_kcal", 0.0) or 0.0)
            - float(getattr(log_data, "exercise_kcal_est", 0.0) or 0.0),
            2,
        )
        return log

    @classmethod
    def persist_block_metrics(
        cls,
        block: WorkoutSessionBlock,
        metrics: WorkoutBlockMetrics,
        *,
        intensity_raw: str | None,
        weight_kg: float,
    ) -> None:
        """Assign calculated metrics to an existing session block entity."""
        block_data = cast(Any, block)
        block_data.intensity_level = metrics.intensity_level
        block_data.intensity_raw = intensity_raw
        block_data.weight_kg_used = float(weight_kg)
        block_data.met_used_min = metrics.met_used_min
        block_data.met_used_max = metrics.met_used_max
        block_data.correction_factor = metrics.correction_factor
        block_data.kcal_min = metrics.kcal_min
        block_data.kcal_max = metrics.kcal_max
        block_data.kcal_est = metrics.kcal_est

    @classmethod
    def _resolve_met_window(
        cls,
        activity: ExerciseActivity,
        intensity_level: str,
    ) -> tuple[float, float]:
        """Return MET min/max range by intensity level."""
        activity_data = cast(Any, activity)
        met_low = float(getattr(activity_data, "met_low", 0.0))
        met_medium = float(getattr(activity_data, "met_medium", 0.0))
        met_high = float(getattr(activity_data, "met_high", 0.0))

        if intensity_level == WorkoutConstants.INTENSITY_LOW:
            return met_low, met_medium
        if intensity_level == WorkoutConstants.INTENSITY_HIGH:
            return met_high, met_high
        return met_medium, met_high

    @classmethod
    def _clamp_correction_factor(cls, value: float) -> float:
        """Clamp correction factor within configured safety limits."""
        return round(
            max(
                WorkoutConstants.MIN_CORRECTION_FACTOR,
                min(WorkoutConstants.MAX_CORRECTION_FACTOR, value),
            ),
            3,
        )

    @classmethod
    def _validate_duration(cls, duration_minutes: int) -> None:
        """Validate workout block duration."""
        if not (
            WorkoutConstants.MIN_DURATION_MINUTES
            <= duration_minutes
            <= WorkoutConstants.MAX_DURATION_MINUTES
        ):
            raise WorkoutValidationError(
                "Duration minutes out of range "
                f"({WorkoutConstants.MIN_DURATION_MINUTES}-{WorkoutConstants.MAX_DURATION_MINUTES})"
            )
