"""Service for building historical progress timeline datasets."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy.orm import Session

from ..config import settings
from ..constants import ProgressEvaluationConstants
from ..db.models import DailyNutrition, Event, SkinfoldMeasurement, User


class ProgressTimelineService:
    """Build chart-ready progress timeline using persisted user data."""

    @classmethod
    def _get_app_timezone(cls):
        try:
            return ZoneInfo(settings.APP_TIMEZONE)
        except ZoneInfoNotFoundError:
            return timezone.utc

    @classmethod
    def _to_utc_bounds(cls, start_local: datetime, end_local: datetime) -> tuple[datetime, datetime]:
        return start_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)

    @classmethod
    def _safe_float(cls, value: Any, default: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @classmethod
    def _normalize_period(cls, periodo: str | None) -> tuple[str, list[str]]:
        warnings: list[str] = []
        normalized = (periodo or "").strip().lower()
        if normalized not in ProgressEvaluationConstants.PERIOD_WINDOW_DAYS:
            warnings.append("Periodo no reconocido. Se usó 'mes' por defecto.")
            return ProgressEvaluationConstants.PERIOD_MONTH, warnings
        return normalized, warnings

    @classmethod
    def build_timeline(cls, db: Session, user: User, periodo: str | None) -> dict[str, Any]:
        normalized_period, warnings = cls._normalize_period(periodo)

        app_tz = cls._get_app_timezone()
        today_local = datetime.now(app_tz).replace(hour=0, minute=0, second=0, microsecond=0)
        period_days = ProgressEvaluationConstants.PERIOD_WINDOW_DAYS[normalized_period]

        range_start_local = today_local - timedelta(days=period_days - 1)
        range_end_exclusive_local = today_local + timedelta(days=1)

        range_start_utc, range_end_exclusive_utc = cls._to_utc_bounds(range_start_local, range_end_exclusive_local)

        # --- Weight series: explicit weight events + skinfold weight values
        weight_events = (
            db.query(Event)
            .filter(
                Event.user_id == user.id,
                Event.event_type == "weight",
                Event.is_deleted == False,  # noqa: E712
                Event.event_timestamp >= range_start_utc,
                Event.event_timestamp < range_end_exclusive_utc,
            )
            .order_by(Event.event_timestamp.asc())
            .all()
        )

        skinfolds = (
            db.query(SkinfoldMeasurement)
            .filter(
                SkinfoldMeasurement.user_id == user.id,
                SkinfoldMeasurement.measured_at >= range_start_utc,
                SkinfoldMeasurement.measured_at < range_end_exclusive_utc,
            )
            .order_by(SkinfoldMeasurement.measured_at.asc())
            .all()
        )

        weight_points: list[dict[str, Any]] = []
        for event in weight_events:
            data = event.data if isinstance(event.data, dict) else {}
            value = data.get("weight_kg")
            if value is None:
                value = data.get("new_weight_kg")
            if value is None:
                continue

            weight_points.append(
                {
                    "fecha": event.event_timestamp.astimezone(app_tz).isoformat(),
                    "valor": round(cls._safe_float(value), 1),
                }
            )

        fat_points: list[dict[str, Any]] = []
        lean_points: list[dict[str, Any]] = []

        for measurement in skinfolds:
            iso_date = measurement.measured_at.astimezone(app_tz).isoformat()
            if measurement.weight_kg is not None:
                weight_points.append(
                    {
                        "fecha": iso_date,
                        "valor": round(cls._safe_float(measurement.weight_kg), 1),
                    }
                )

            fat_points.append(
                {
                    "fecha": iso_date,
                    "valor": round(cls._safe_float(measurement.body_fat_percent), 1),
                }
            )

            lean_points.append(
                {
                    "fecha": iso_date,
                    "valor": round(cls._safe_float(measurement.fat_free_mass_percent), 1),
                }
            )

        weight_points = sorted(weight_points, key=lambda point: point["fecha"])

        if not weight_points and user.weight is not None:
            warnings.append("No hay histórico de peso en el periodo. Se muestra el peso actual como referencia.")
            weight_points = [
                {
                    "fecha": datetime.now(app_tz).isoformat(),
                    "valor": round(cls._safe_float(user.weight), 1),
                }
            ]

        if not fat_points:
            warnings.append("No hay mediciones de % grasa en el periodo seleccionado.")
        if not lean_points:
            warnings.append("No hay mediciones de % masa magra en el periodo seleccionado.")

        # --- Daily nutrition series
        nutrition_rows = (
            db.query(DailyNutrition)
            .filter(
                DailyNutrition.user_id == user.id,
                DailyNutrition.date >= range_start_utc,
                DailyNutrition.date < range_end_exclusive_utc,
            )
            .order_by(DailyNutrition.date.asc())
            .all()
        )

        calories_target = cls._safe_float(getattr(user, "target_calories", None))
        if calories_target <= 0:
            calories_target = cls._safe_float(getattr(user, "daily_caloric_expenditure", None), default=2000.0)

        calories_points: list[dict[str, Any]] = []
        macro_percentage_points: list[dict[str, Any]] = []

        for row in nutrition_rows:
            iso_date = row.date.astimezone(app_tz).isoformat()

            carbs_percentage = 0.0 if row.carbs_target <= 0 else (row.carbs_consumed / row.carbs_target) * 100.0
            protein_percentage = 0.0 if row.protein_target <= 0 else (row.protein_consumed / row.protein_target) * 100.0
            fat_percentage = 0.0 if row.fat_target <= 0 else (row.fat_consumed / row.fat_target) * 100.0

            calories_points.append(
                {
                    "fecha": iso_date,
                    "consumidas": round(cls._safe_float(row.total_calories), 1),
                    "meta": round(calories_target, 1),
                }
            )

            macro_percentage_points.append(
                {
                    "fecha": iso_date,
                    "carbs": round(carbs_percentage, 1),
                    "protein": round(protein_percentage, 1),
                    "fat": round(fat_percentage, 1),
                }
            )

        if not calories_points:
            warnings.append("No hay consumo calórico diario registrado en el periodo seleccionado.")

        # Weekly summary for goals vs real consumption
        week_start_local = today_local - timedelta(days=6)
        week_start_utc, week_end_exclusive_utc = cls._to_utc_bounds(week_start_local, range_end_exclusive_local)

        week_rows = (
            db.query(DailyNutrition)
            .filter(
                DailyNutrition.user_id == user.id,
                DailyNutrition.date >= week_start_utc,
                DailyNutrition.date < week_end_exclusive_utc,
            )
            .all()
        )

        calories_week_real = round(sum(cls._safe_float(row.total_calories) for row in week_rows), 1)
        calories_week_goal = round(calories_target * 7, 1)

        return {
            "periodo": normalized_period,
            "rango_inicio": range_start_local.date().isoformat(),
            "rango_fin": today_local.date().isoformat(),
            "series": {
                "peso": weight_points,
                "porcentaje_grasa": fat_points,
                "porcentaje_masa_magra": lean_points,
                "calorias_diarias": calories_points,
                "macros_porcentaje": macro_percentage_points,
            },
            "resumen": {
                "calorias_semana_real": calories_week_real,
                "calorias_semana_meta": calories_week_goal,
            },
            "advertencias": warnings,
        }
