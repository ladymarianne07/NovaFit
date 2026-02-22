"""Pure progress evaluation service based on objective, period and historical body metrics."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..constants import ProgressEvaluationConstants


OBJETIVO_ALIASES = {
    "perdida_grasa": "fat_loss",
    "mantenimiento": "maintenance",
    "aumento_muscular": "muscle_gain",
    "recomposicion": "body_recomp",
    "rendimiento": "performance",
    # Internal aliases used in the existing backend
    "fat_loss": "fat_loss",
    "maintenance": "maintenance",
    "muscle_gain": "muscle_gain",
    "body_recomp": "body_recomp",
    "performance": "performance",
}


def _parse_date(value: Any) -> Optional[datetime]:
    """Parse supported date formats into datetime."""
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            normalized = value.replace("Z", "+00:00")
            return datetime.fromisoformat(normalized)
        except ValueError:
            return None
    return None


def _safe_float(value: Any) -> Optional[float]:
    """Return float value or None when conversion fails."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _apply_noise_filter(value: Optional[float], threshold: float) -> Optional[float]:
    """Ignore small fluctuations considered normal day-to-day noise."""
    if value is None:
        return None
    if abs(value) < threshold:
        return 0.0
    return value


def _round1(value: Optional[float]) -> Optional[float]:
    """Round helper for user-facing values."""
    if value is None:
        return None
    return round(value, 1)


def _normalize_period(periodo: Optional[str]) -> str:
    """Normalize period to a supported value, defaulting to month."""
    raw = (periodo or "").strip().lower()
    if raw in ProgressEvaluationConstants.PERIOD_WINDOW_DAYS:
        return raw
    return ProgressEvaluationConstants.PERIOD_MONTH


def _avg_metric(records: List[Dict[str, Any]], key: str) -> Optional[float]:
    """Average a metric using only valid numeric records."""
    values = [_safe_float(item.get(key)) for item in records]
    valid_values = [value for value in values if value is not None]
    if not valid_values:
        return None
    return sum(valid_values) / len(valid_values)


def _clamp_score(score: float) -> float:
    """Clamp score to configured output limits."""
    return max(ProgressEvaluationConstants.MIN_SCORE, min(ProgressEvaluationConstants.MAX_SCORE, score))


def _classify_score(score: float) -> str:
    """Map numeric score to a readable status."""
    if score > ProgressEvaluationConstants.POSITIVE_SCORE_THRESHOLD:
        return "Progreso positivo"
    if score >= ProgressEvaluationConstants.STABLE_SCORE_MIN:
        return "Estable"
    return "Desviación del objetivo"


def _trend_delta(
    baseline_delta: Optional[float],
    recent_delta: Optional[float],
    threshold: float,
) -> Optional[float]:
    """Blend long-term and recent trend deltas, then filter tiny fluctuations."""
    if baseline_delta is None:
        return None
    if recent_delta is None:
        blended = baseline_delta
    else:
        blended = (
            baseline_delta * ProgressEvaluationConstants.BASELINE_WEIGHT_FACTOR
            + recent_delta * ProgressEvaluationConstants.RECENT_WEIGHT_FACTOR
        )
    return _apply_noise_filter(blended, threshold)


def _window_records(records: List[Dict[str, Any]], periodo: str) -> tuple[List[Dict[str, Any]], bool]:
    """Return period-filtered records and fallback flag.

    Fallback flag is True when there are not enough in-range records and full history is used.
    """
    if not records:
        return [], False

    latest_date = records[-1]["fecha"]
    window_days = ProgressEvaluationConstants.PERIOD_WINDOW_DAYS[periodo]
    start_date = latest_date - timedelta(days=window_days)
    in_window = [item for item in records if item["fecha"] >= start_date]

    if len(in_window) >= ProgressEvaluationConstants.MIN_HISTORY_RECORDS:
        return in_window, False

    return records, True


def _split_initial_final(records: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Split records into initial and final groups for trend averaging."""
    split_index = len(records) // 2
    if split_index <= 0:
        split_index = 1
    initial = records[:split_index]
    final = records[split_index:]
    if not final:
        final = records[-1:]
    return initial, final


def evaluar_progreso(objetivo: str, periodo: str, historial: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Evaluate physical progress trend based on objective and available body metrics.

    This function is pure (no DB side effects) and designed for unit testing.
    """
    advertencias: List[str] = []
    periodo_normalizado = _normalize_period(periodo)

    if len(historial) < ProgressEvaluationConstants.MIN_HISTORY_RECORDS:
        return {
            "periodo": periodo_normalizado,
            "score": 0.0,
            "estado": "Estable",
            "resumen": "No hay suficientes registros para evaluar tendencia. Se requieren al menos 2 mediciones.",
            "metricas": {"deltaPeso": 0.0, "deltaGrasa": None, "deltaMagra": None},
            "advertencias": ["Datos insuficientes para evaluar progreso."],
        }

    objetivo_normalizado = OBJETIVO_ALIASES.get((objetivo or "").strip().lower())
    if not objetivo_normalizado:
        objetivo_normalizado = "maintenance"
        advertencias.append("Objetivo no reconocido. Se evaluó con criterios de mantenimiento.")

    parsed_history: List[Dict[str, Any]] = []
    for item in historial:
        parsed_date = _parse_date(item.get("fecha"))
        if parsed_date is None:
            continue
        parsed_history.append(
            {
                "fecha": parsed_date,
                "peso": _safe_float(item.get("peso")),
                "porcentaje_grasa": _safe_float(item.get("porcentaje_grasa")),
                "porcentaje_masa_magra": _safe_float(item.get("porcentaje_masa_magra")),
            }
        )

    parsed_history = [row for row in parsed_history if row["peso"] is not None]

    if len(parsed_history) < ProgressEvaluationConstants.MIN_HISTORY_RECORDS:
        return {
            "periodo": periodo_normalizado,
            "score": 0.0,
            "estado": "Estable",
            "resumen": "No hay suficientes registros válidos para evaluar tendencia.",
            "metricas": {"deltaPeso": 0.0, "deltaGrasa": None, "deltaMagra": None},
            "advertencias": ["Datos insuficientes o fechas inválidas en el historial."],
        }

    parsed_history.sort(key=lambda row: row["fecha"])

    scoped_history, used_fallback_window = _window_records(parsed_history, periodo_normalizado)
    if used_fallback_window:
        advertencias.append(
            "No hay suficientes datos en el periodo solicitado; se usó el rango disponible más cercano."
        )

    if len(scoped_history) < ProgressEvaluationConstants.MIN_HISTORY_RECORDS:
        return {
            "periodo": periodo_normalizado,
            "score": 0.0,
            "estado": "Estable",
            "resumen": "No hay suficientes registros para evaluar tendencia en el periodo seleccionado.",
            "metricas": {"deltaPeso": 0.0, "deltaGrasa": None, "deltaMagra": None},
            "advertencias": ["Datos insuficientes para el periodo seleccionado."],
        }

    initial_group, final_group = _split_initial_final(scoped_history)

    initial_avg = {
        "peso": _avg_metric(initial_group, "peso"),
        "porcentaje_grasa": _avg_metric(initial_group, "porcentaje_grasa"),
        "porcentaje_masa_magra": _avg_metric(initial_group, "porcentaje_masa_magra"),
    }
    final_avg = {
        "peso": _avg_metric(final_group, "peso"),
        "porcentaje_grasa": _avg_metric(final_group, "porcentaje_grasa"),
        "porcentaje_masa_magra": _avg_metric(final_group, "porcentaje_masa_magra"),
    }

    weight_noise_threshold = ProgressEvaluationConstants.PERIOD_WEIGHT_FLUCTUATION_KG[periodo_normalizado]
    body_comp_noise_threshold = ProgressEvaluationConstants.PERIOD_BODY_COMP_FLUCTUATION_PERCENT[periodo_normalizado]

    delta_peso_base = 0.0
    if initial_avg["peso"] is not None and final_avg["peso"] is not None:
        delta_peso_base = final_avg["peso"] - initial_avg["peso"]

    delta_grasa_base = None
    if initial_avg["porcentaje_grasa"] is not None and final_avg["porcentaje_grasa"] is not None:
        delta_grasa_base = final_avg["porcentaje_grasa"] - initial_avg["porcentaje_grasa"]

    delta_magra_base = None
    if (
        initial_avg["porcentaje_masa_magra"] is not None
        and final_avg["porcentaje_masa_magra"] is not None
    ):
        delta_magra_base = final_avg["porcentaje_masa_magra"] - initial_avg["porcentaje_masa_magra"]

    delta_peso = _apply_noise_filter(delta_peso_base, weight_noise_threshold)
    delta_grasa = _apply_noise_filter(delta_grasa_base, body_comp_noise_threshold)
    delta_magra = _apply_noise_filter(delta_magra_base, body_comp_noise_threshold)

    score_raw = 0.0
    resumen = ""

    if objetivo_normalizado == "fat_loss":
        if delta_grasa is not None:
            score_raw = (-delta_grasa * 60.0) + ((-delta_peso * 10.0) if delta_peso is not None else 0.0)
            if delta_magra is not None:
                score_raw += delta_magra * 30.0
            else:
                advertencias.append("No hay porcentaje de masa magra para verificar preservación muscular.")

            resumen = (
                f"En el periodo analizado, el peso cambió {_round1(delta_peso_base)} kg y la grasa corporal "
                f"{_round1(delta_grasa_base)} puntos."
            )
        else:
            if delta_peso is None:
                delta_peso = 0.0
            score_raw = -delta_peso * 100.0
            advertencias.append(
                "No hay datos de composición corporal (grasa/magra). El análisis se basa solo en peso."
            )
            resumen = (
                f"Se observa una variación de peso de {_round1(delta_peso_base)} kg en el periodo. "
                "Sin datos de grasa corporal, no puede confirmarse la calidad del cambio."
            )

    elif objetivo_normalizado == "maintenance":
        base_weight = initial_avg["peso"] or 0.0
        final_weight = final_avg["peso"] or base_weight
        peso_pct = 0.0 if base_weight == 0 else ((final_weight - base_weight) / base_weight) * 100.0
        peso_pct = _apply_noise_filter(peso_pct, weight_noise_threshold)

        penalty = 0.0
        if peso_pct is not None and abs(peso_pct) > ProgressEvaluationConstants.MAINTENANCE_MAX_WEIGHT_DEVIATION_PERCENT:
            penalty += (abs(peso_pct) - ProgressEvaluationConstants.MAINTENANCE_MAX_WEIGHT_DEVIATION_PERCENT) * 20.0

        if delta_grasa is not None:
            if abs(delta_grasa) > ProgressEvaluationConstants.MAINTENANCE_MAX_FAT_DEVIATION_PERCENT:
                penalty += (abs(delta_grasa) - ProgressEvaluationConstants.MAINTENANCE_MAX_FAT_DEVIATION_PERCENT) * 30.0
        else:
            advertencias.append("No hay % de grasa para una evaluación completa de mantenimiento.")

        if delta_magra is not None and abs(delta_magra) > 1.0:
            penalty += (abs(delta_magra) - 1.0) * 20.0

        score_raw = 30.0 - penalty
        resumen = (
            f"En mantenimiento, el peso cambió {_round1(delta_peso_base)} kg "
            f"({round(peso_pct or 0.0, 1)}%)."
        )

    elif objetivo_normalizado == "muscle_gain":
        if delta_magra is not None:
            score_raw = (delta_magra * 60.0) + ((delta_peso * 20.0) if delta_peso is not None else 0.0)
            if delta_grasa is not None:
                score_raw += -delta_grasa * 20.0
            else:
                advertencias.append("No hay % de grasa para controlar ganancia de grasa no deseada.")

            resumen = (
                f"La masa magra cambió {_round1(delta_magra_base)} puntos y el peso {_round1(delta_peso_base)} kg "
                "en el periodo, consistente con objetivo de aumento muscular."
            )
        else:
            if delta_peso is None:
                delta_peso = 0.0
            score_raw = delta_peso * 100.0
            advertencias.append("No hay % de masa magra. El análisis se basa solo en variación de peso.")
            resumen = (
                f"El peso cambió {_round1(delta_peso_base)} kg. "
                "Faltan datos de masa magra para confirmar progreso de hipertrofia."
            )

    elif objetivo_normalizado == "body_recomp":
        if delta_grasa is None or delta_magra is None:
            advertencias.append("La recomposición requiere % de grasa y % de masa magra en el historial.")
            score_raw = 0.0
            resumen = (
                "Datos insuficientes para evaluar recomposición corporal. "
                "Se necesitan mediciones de grasa y masa magra en al menos 2 registros."
            )
        else:
            score_raw = (-delta_grasa * 50.0) + (delta_magra * 50.0)
            resumen = (
                f"En el periodo, la grasa cambió {_round1(delta_grasa_base)} puntos y la masa magra "
                f"{_round1(delta_magra_base)} puntos, acorde a recomposición corporal."
            )

    elif objetivo_normalizado == "performance":
        if delta_grasa is not None and delta_magra is not None:
            score_raw = (-abs(delta_peso or 0.0) * 10.0) + (-delta_grasa * 35.0) + (delta_magra * 35.0)
            resumen = (
                "La evaluación de rendimiento se apoya en estabilidad/composición corporal "
                f"(peso {_round1(delta_peso_base)} kg, grasa {_round1(delta_grasa_base)} pts, "
                f"magra {_round1(delta_magra_base)} pts)."
            )
        else:
            score_raw = -abs(delta_peso or 0.0) * 20.0
            advertencias.append("Sin datos completos de composición corporal, la evaluación de rendimiento es parcial.")
            resumen = (
                f"El peso cambió {_round1(delta_peso_base)} kg. "
                "Para evaluar rendimiento con mayor precisión, añade métricas deportivas (carga, tiempos, repeticiones)."
            )

        advertencias.append("Sugerencia: incorporar métricas deportivas para una evaluación de rendimiento más robusta.")

    period_multiplier = ProgressEvaluationConstants.PERIOD_SCORE_MULTIPLIER[periodo_normalizado]
    score = round(_clamp_score(score_raw * period_multiplier), 1)
    estado = _classify_score(score)

    # Period-specific contextual messaging
    if periodo_normalizado == ProgressEvaluationConstants.PERIOD_WEEK:
        resumen += (
            " Variación semanal observada. Recuerda que los cambios a corto plazo "
            "pueden reflejar ajustes de líquidos y glucógeno."
        )
    elif periodo_normalizado == ProgressEvaluationConstants.PERIOD_MONTH:
        resumen += " La tendencia mensual es consistente con tu objetivo."
    else:
        lean_mass_initial_kg = None
        lean_mass_final_kg = None
        if (
            initial_avg["peso"] is not None
            and initial_avg["porcentaje_masa_magra"] is not None
            and final_avg["peso"] is not None
            and final_avg["porcentaje_masa_magra"] is not None
        ):
            lean_mass_initial_kg = initial_avg["peso"] * (initial_avg["porcentaje_masa_magra"] / 100.0)
            lean_mass_final_kg = final_avg["peso"] * (final_avg["porcentaje_masa_magra"] / 100.0)

        significant_annual = False
        if delta_grasa_base is not None and abs(delta_grasa_base) >= ProgressEvaluationConstants.ANNUAL_SIGNIFICANT_FAT_CHANGE_PERCENT:
            significant_annual = True
        if lean_mass_initial_kg is not None and lean_mass_final_kg is not None:
            if abs(lean_mass_final_kg - lean_mass_initial_kg) >= ProgressEvaluationConstants.ANNUAL_SIGNIFICANT_LEAN_MASS_KG:
                significant_annual = True

        if significant_annual:
            resumen += " Transformación anual significativa detectada."
        else:
            resumen += " Evaluación anual completada con enfoque estructural de largo plazo."

    return {
        "periodo": periodo_normalizado,
        "score": score,
        "estado": estado,
        "resumen": resumen,
        "metricas": {
            "deltaPeso": _round1(delta_peso if delta_peso is not None else 0.0),
            "deltaGrasa": _round1(delta_grasa),
            "deltaMagra": _round1(delta_magra),
        },
        "advertencias": advertencias,
    }


def evaluarProgreso(objetivo: str, periodo: str, historial: List[Dict[str, Any]]) -> Dict[str, Any]:
    """CamelCase wrapper required by product request."""
    return evaluar_progreso(objetivo=objetivo, periodo=periodo, historial=historial)
