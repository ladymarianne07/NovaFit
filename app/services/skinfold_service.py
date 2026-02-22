import re
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from ..constants import SkinfoldConstants
from ..core.custom_exceptions import InputValidationError
from ..db.models import SkinfoldMeasurement, User
from ..schemas.skinfold import SkinfoldCalculationRequest, SkinfoldValues, Sex


class SkinfoldService:
    """Business logic for skinfold parsing, validation and calculations."""

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _round_percent(value: float) -> float:
        return round(value, SkinfoldConstants.ROUND_PERCENT_DECIMALS)

    @staticmethod
    def _round_kg(value: float) -> float:
        return round(value, SkinfoldConstants.ROUND_KG_DECIMALS)

    @staticmethod
    def _has_all(values: SkinfoldCalculationRequest, names: tuple[str, ...]) -> bool:
        return all(getattr(values, n) is not None for n in names)

    @staticmethod
    def _sum_values(values: SkinfoldCalculationRequest, names: tuple[str, ...]) -> float:
        return sum(float(getattr(values, n)) for n in names)

    @classmethod
    def calculate(cls, payload: SkinfoldCalculationRequest) -> dict:
        warnings: list[str] = []

        if payload.age_years < SkinfoldConstants.RECOMMENDED_MIN_AGE or payload.age_years > SkinfoldConstants.RECOMMENDED_MAX_AGE:
            warnings.append("La edad está fuera del rango validado clásico de la ecuación (18-61). Interpretar con cautela.")

        for site in SkinfoldConstants.JP7_SITE_NAMES:
            value = getattr(payload, site)
            if value is not None and value > SkinfoldConstants.SOFT_WARNING_SKINFOLD_MM:
                warnings.append(f"{site.replace('_mm', '')}: valor alto (>60 mm), revisar técnica de medición.")

        if cls._has_all(payload, SkinfoldConstants.JP7_SITE_NAMES):
            method = "Jackson-Pollock 7 + Siri"
            skinfold_sum = cls._sum_values(payload, SkinfoldConstants.JP7_SITE_NAMES)

            if payload.sex == Sex.MALE:
                body_density = (
                    1.112
                    - (0.00043499 * skinfold_sum)
                    + (0.00000055 * skinfold_sum * skinfold_sum)
                    - (0.00028826 * payload.age_years)
                )
            else:
                body_density = (
                    1.097
                    - (0.00046971 * skinfold_sum)
                    + (0.00000056 * skinfold_sum * skinfold_sum)
                    - (0.00012828 * payload.age_years)
                )
        elif cls._has_all(payload, SkinfoldConstants.JP3_SITE_NAMES):
            method = "Jackson-Pollock 3 + Siri (fallback)"
            skinfold_sum = cls._sum_values(payload, SkinfoldConstants.JP3_SITE_NAMES)
            warnings.append("Se usó fallback JP3 por pliegues incompletos para JP7. JP7 ofrece mejor precisión dentro de métodos con caliper.")

            if payload.sex == Sex.MALE:
                body_density = (
                    1.10938
                    - (0.0008267 * skinfold_sum)
                    + (0.0000016 * skinfold_sum * skinfold_sum)
                    - (0.0002574 * payload.age_years)
                )
            else:
                body_density = (
                    1.0994921
                    - (0.0009929 * skinfold_sum)
                    + (0.0000023 * skinfold_sum * skinfold_sum)
                    - (0.0001392 * payload.age_years)
                )
        else:
            raise InputValidationError(
                "skinfolds",
                "Faltan pliegues para JP7. Completa los 7 sitios o al menos pecho/abdomen/muslo para fallback JP3."
            )

        if body_density <= 0:
            raise InputValidationError("body_density", "Invalid body density. Revisa las mediciones ingresadas.")

        body_fat_percent_raw = (495 / body_density) - 450
        ffm_percent_raw = 100 - body_fat_percent_raw

        if body_fat_percent_raw < 0 or body_fat_percent_raw > 70:
            warnings.append("El % de grasa está fuera del rango habitual (0-70). Revisar mediciones y técnica.")

        fat_mass_kg = None
        lean_mass_kg = None
        if payload.weight_kg is not None:
            fat_mass_kg = payload.weight_kg * (body_fat_percent_raw / 100)
            lean_mass_kg = payload.weight_kg - fat_mass_kg

        return {
            "method": method,
            "measured_at": datetime.now(timezone.utc),
            "sum_of_skinfolds_mm": round(skinfold_sum, 2),
            "body_density": round(body_density, SkinfoldConstants.ROUND_DENSITY_DECIMALS),
            "body_fat_percent": cls._round_percent(body_fat_percent_raw),
            "fat_free_mass_percent": cls._round_percent(ffm_percent_raw),
            "fat_mass_kg": cls._round_kg(fat_mass_kg) if fat_mass_kg is not None else None,
            "lean_mass_kg": cls._round_kg(lean_mass_kg) if lean_mass_kg is not None else None,
            "warnings": warnings,
        }

    @staticmethod
    def parse_ai_text(text: str) -> tuple[SkinfoldValues, list[str]]:
        normalized = text.lower()
        warnings: list[str] = []

        alias_map = {
            "chest_mm": ["pecho", "pectoral", "chest"],
            "midaxillary_mm": ["axilar", "midaxilar", "midaxillary", "axila"],
            "triceps_mm": ["triceps", "tríceps"],
            "subscapular_mm": ["subescapular", "subscapular"],
            "abdomen_mm": ["abdomen", "abdominal"],
            "suprailiac_mm": ["suprailiaco", "suprailíaco", "suprailiac"],
            "thigh_mm": ["muslo", "thigh"],
        }

        result: dict[str, Optional[float]] = {site: None for site in SkinfoldConstants.JP7_SITE_NAMES}

        for site, aliases in alias_map.items():
            for alias in aliases:
                pattern = rf"{re.escape(alias)}[^0-9]*(\d+(?:[\.,]\d+)?(?:\s*/\s*\d+(?:[\.,]\d+)?){{0,2}})"
                match = re.search(pattern, normalized)
                if not match:
                    continue

                raw = match.group(1).replace(",", ".")
                parts = [float(p.strip()) for p in raw.split("/")]
                result[site] = round(sum(parts) / len(parts), 2)
                if len(parts) > 1:
                    warnings.append(f"{alias}: se promediaron {len(parts)} lecturas automáticamente.")
                break

        return SkinfoldValues(**result), warnings

    def save_measurement(
        self,
        user: User,
        payload: SkinfoldCalculationRequest,
        result: dict,
    ) -> SkinfoldMeasurement:
        measurement = SkinfoldMeasurement(
            user_id=user.id,
            method=result["method"],
            measurement_unit=payload.measurement_unit,
            measured_at=result["measured_at"],
            sex=payload.sex.value,
            age_years=payload.age_years,
            weight_kg=payload.weight_kg,
            chest_mm=payload.chest_mm,
            midaxillary_mm=payload.midaxillary_mm,
            triceps_mm=payload.triceps_mm,
            subscapular_mm=payload.subscapular_mm,
            abdomen_mm=payload.abdomen_mm,
            suprailiac_mm=payload.suprailiac_mm,
            thigh_mm=payload.thigh_mm,
            sum_of_skinfolds_mm=result["sum_of_skinfolds_mm"],
            body_density=result["body_density"],
            body_fat_percent=result["body_fat_percent"],
            fat_free_mass_percent=result["fat_free_mass_percent"],
            fat_mass_kg=result["fat_mass_kg"],
            lean_mass_kg=result["lean_mass_kg"],
            warnings=result["warnings"],
        )

        self.db.add(measurement)
        self.db.commit()
        self.db.refresh(measurement)
        return measurement

    def get_history(self, user_id: int, limit: int = 20) -> list[SkinfoldMeasurement]:
        return (
            self.db.query(SkinfoldMeasurement)
            .filter(SkinfoldMeasurement.user_id == user_id)
            .order_by(SkinfoldMeasurement.measured_at.desc())
            .limit(limit)
            .all()
        )
