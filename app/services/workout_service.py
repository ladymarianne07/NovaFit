"""Workout Service - MET based calculations and workout persistence helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any, cast
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..config import settings
from ..constants import WorkoutConstants
from ..core.custom_exceptions import (
    WorkoutActivityNotFoundError,
    WorkoutValidationError,
    WorkoutWeightRequiredError,
)
from ..db.models import (
    DailyNutrition,
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
    def validate_session_status(cls, status: str) -> str:
        """Validate and normalize workout session status."""
        normalized_status = status.strip().lower()
        if normalized_status not in WorkoutConstants.VALID_SESSION_STATUS:
            raise WorkoutValidationError(
                f"Invalid workout status '{status}'. Valid: {sorted(WorkoutConstants.VALID_SESSION_STATUS)}"
            )
        return normalized_status

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
    def create_session(
        cls,
        db: Session,
        *,
        user_id: int,
        session_date: date,
        source: str,
        status: str,
        blocks_data: list[dict[str, Any]],
        weight_kg: float | None,
        raw_input: str | None = None,
        ai_output: dict[str, Any] | None = None,
    ) -> WorkoutSession:
        """Create a workout session with calculated block and session totals."""
        if not blocks_data:
            raise WorkoutValidationError("Workout session must include at least one block")

        normalized_source = cls.validate_session_source(source)
        normalized_status = cls.validate_session_status(status)

        session = WorkoutSession(
            user_id=user_id,
            session_date=session_date,
            source=normalized_source,
            status=normalized_status,
            raw_input=raw_input,
            ai_output=ai_output,
        )

        session_data = cast(Any, session)
        session_blocks: list[WorkoutSessionBlock] = []

        for index, block_data in enumerate(blocks_data, start=1):
            activity_query = str(block_data.get("activity") or block_data.get("activity_key") or "").strip()
            if not activity_query:
                raise WorkoutValidationError("Each workout block requires 'activity' or 'activity_key'")

            duration_minutes = int(block_data.get("duration_minutes", 0))
            activity = cls.resolve_activity(db, activity_query)
            intensity_raw = cast(str | None, block_data.get("intensity") or block_data.get("intensity_raw"))
            effective_factor = cls.get_effective_correction_factor(
                db=db,
                user_id=user_id,
                session_date=session_date,
                activity=activity,
            )

            metrics = cls.calculate_block_metrics(
                activity=activity,
                duration_minutes=duration_minutes,
                weight_kg=weight_kg,
                intensity_level=intensity_raw,
                correction_factor=effective_factor,
            )

            block = WorkoutSessionBlock(
                block_order=index,
                duration_minutes=duration_minutes,
                activity_id=cast(Any, activity).id,
            )
            cls.persist_block_metrics(
                block,
                metrics,
                intensity_raw=intensity_raw,
                weight_kg=float(weight_kg or 0.0),
            )
            session_blocks.append(block)

        session_data.blocks = session_blocks
        cls.recalculate_session_totals(session)

        db.add(session)
        db.flush()

        cls.refresh_daily_energy_log(db=db, user_id=user_id, log_date=session_date)
        db.commit()
        db.refresh(session)
        return session

    @classmethod
    def refresh_daily_energy_log(
        cls,
        db: Session,
        *,
        user_id: int,
        log_date: date,
    ) -> ExerciseDailyEnergyLog:
        """Recompute daily energy totals from all sessions for a date."""
        aggregate = (
            db.query(
                func.coalesce(func.sum(WorkoutSession.total_kcal_min), 0.0),
                func.coalesce(func.sum(WorkoutSession.total_kcal_max), 0.0),
                func.coalesce(func.sum(WorkoutSession.total_kcal_est), 0.0),
            )
            .filter(
                WorkoutSession.user_id == user_id,
                WorkoutSession.session_date == log_date,
            )
            .first()
        )

        total_min = float(aggregate[0] or 0.0) if aggregate else 0.0
        total_max = float(aggregate[1] or 0.0) if aggregate else 0.0
        total_est = float(aggregate[2] or 0.0) if aggregate else 0.0
        intake_kcal = cls.get_daily_intake_kcal(db=db, user_id=user_id, tracking_date=log_date)

        return cls.upsert_daily_energy_log(
            db,
            user_id=user_id,
            log_date=log_date,
            exercise_kcal_min=total_min,
            exercise_kcal_max=total_max,
            exercise_kcal_est=total_est,
            intake_kcal=intake_kcal,
        )

    @classmethod
    def get_daily_energy(cls, db: Session, *, user_id: int, log_date: date) -> ExerciseDailyEnergyLog:
        """Get or rebuild daily energy log for a specific date."""
        return cls.refresh_daily_energy_log(db=db, user_id=user_id, log_date=log_date)

    @classmethod
    def list_sessions(
        cls,
        db: Session,
        *,
        user_id: int,
        session_date: date | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[WorkoutSession]:
        """List workout sessions for a user, optionally filtered by date."""
        query = db.query(WorkoutSession).filter(WorkoutSession.user_id == user_id)
        if session_date is not None:
            query = query.filter(WorkoutSession.session_date == session_date)

        return (
            query.order_by(WorkoutSession.session_date.desc(), WorkoutSession.id.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    @classmethod
    def delete_session(cls, db: Session, *, user_id: int, session_id: int) -> bool:
        """Delete a workout session and recalculate daily totals for its date."""
        session = (
            db.query(WorkoutSession)
            .filter(
                WorkoutSession.id == session_id,
                WorkoutSession.user_id == user_id,
            )
            .first()
        )
        if session is None:
            return False

        session_data = cast(Any, session)
        log_date = cast(date, getattr(session_data, "session_date"))
        db.delete(session)
        db.flush()

        cls.refresh_daily_energy_log(db=db, user_id=user_id, log_date=log_date)
        db.commit()
        return True

    @classmethod
    def get_daily_intake_kcal(cls, db: Session, *, user_id: int, tracking_date: date) -> float:
        """Resolve daily nutrition intake calories for a local day in app timezone."""
        start_utc, end_utc = cls._get_utc_day_bounds(tracking_date)
        value = (
            db.query(func.coalesce(func.sum(DailyNutrition.total_calories), 0.0))
            .filter(
                DailyNutrition.user_id == user_id,
                DailyNutrition.date >= start_utc,
                DailyNutrition.date < end_utc,
            )
            .scalar()
        )
        return round(float(value or 0.0), 2)

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

    @classmethod
    def _get_app_timezone(cls):
        """Return configured app timezone; fallback to UTC when invalid."""
        try:
            return ZoneInfo(settings.APP_TIMEZONE)
        except ZoneInfoNotFoundError:
            return timezone.utc

    @classmethod
    def _get_utc_day_bounds(cls, tracking_date: date) -> tuple[datetime, datetime]:
        """Compute UTC [start, end) range for a local day in app timezone."""
        app_tz = cls._get_app_timezone()
        local_start = datetime.combine(tracking_date, datetime.min.time()).replace(tzinfo=app_tz)
        local_end = local_start + timedelta(days=1)
        return local_start.astimezone(timezone.utc), local_end.astimezone(timezone.utc)
