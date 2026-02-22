"""Unit tests for adaptive physical progress evaluation service."""

from app.services.progress_evaluation_service import evaluar_progreso, evaluarProgreso


def _row(fecha: str, peso: float, grasa: float | None = None, magra: float | None = None) -> dict:
    return {
        "fecha": fecha,
        "peso": peso,
        "porcentaje_grasa": grasa,
        "porcentaje_masa_magra": magra,
    }


def test_returns_warning_with_less_than_two_records():
    result = evaluar_progreso(
        objetivo="perdida_grasa",
        periodo="mes",
        historial=[_row("2026-01-01T00:00:00", 80.0, 25.0, 40.0)],
    )

    assert result["periodo"] == "mes"
    assert result["score"] == 0.0
    assert result["estado"] == "Estable"
    assert "metricas" in result
    assert len(result["advertencias"]) >= 1


def test_fat_loss_with_complete_data_scores_positive():
    historial = [
        _row("2026-01-01T00:00:00", 80.0, 25.0, 40.0),
        _row("2026-01-20T00:00:00", 79.3, 24.3, 40.2),
        _row("2026-02-10T00:00:00", 78.8, 23.9, 40.4),
        _row("2026-02-20T00:00:00", 78.2, 23.4, 40.7),
    ]

    result = evaluar_progreso(objetivo="perdida_grasa", periodo="mes", historial=historial)

    assert result["score"] > 20
    assert result["estado"] == "Progreso positivo"


def test_fat_loss_without_body_composition_uses_weight_only_and_warns():
    historial = [
        _row("2026-01-01T00:00:00", 90.0),
        _row("2026-01-15T00:00:00", 88.9),
        _row("2026-02-20T00:00:00", 87.8),
    ]

    result = evaluar_progreso(objetivo="perdida_grasa", periodo="mes", historial=historial)

    assert result["score"] > 20
    assert any("composición corporal" in warning.lower() for warning in result["advertencias"])


def test_recomposition_requires_fat_and_lean_data():
    historial = [
        _row("2026-01-01T00:00:00", 70.0, None, 43.0),
        _row("2026-02-01T00:00:00", 69.8, None, 43.5),
    ]

    result = evaluar_progreso(objetivo="recomposicion", periodo="mes", historial=historial)

    assert result["score"] == 0.0
    assert result["estado"] == "Estable"
    assert any("recomposición" in warning.lower() for warning in result["advertencias"])


def test_small_fluctuations_are_ignored():
    historial = [
        _row("2026-01-01T00:00:00", 75.0, 20.0, 45.0),
        _row("2026-02-01T00:00:00", 75.2, 20.2, 45.1),
    ]

    result = evaluar_progreso(objetivo="mantenimiento", periodo="mes", historial=historial)

    assert -20 <= result["score"] <= 40
    assert result["estado"] in {"Estable", "Progreso positivo"}


def test_muscle_gain_with_lean_increase_scores_positive():
    historial = [
        _row("2026-01-01T00:00:00", 72.0, 16.0, 48.0),
        _row("2026-01-20T00:00:00", 72.8, 16.1, 48.6),
        _row("2026-02-20T00:00:00", 73.7, 16.3, 49.1),
    ]

    result = evaluarProgreso(objetivo="aumento_muscular", periodo="mes", historial=historial)

    assert result["score"] > 20
    assert result["estado"] == "Progreso positivo"


def test_score_is_clamped_to_valid_range():
    historial = [
        _row("2026-01-01T00:00:00", 95.0, 35.0, 35.0),
        _row("2026-02-20T00:00:00", 70.0, 10.0, 50.0),
    ]

    result = evaluar_progreso(objetivo="perdida_grasa", periodo="mes", historial=historial)

    assert -100.0 <= result["score"] <= 100.0


def test_week_period_applies_conservative_multiplier_and_message():
    historial = [
        _row("2026-02-14T00:00:00", 85.0, 28.0, 38.0),
        _row("2026-02-16T00:00:00", 84.4, 27.4, 38.3),
        _row("2026-02-20T00:00:00", 84.0, 27.0, 38.6),
    ]

    result = evaluar_progreso(objetivo="perdida_grasa", periodo="semana", historial=historial)
    assert result["periodo"] == "semana"
    assert "líquidos y glucógeno" in result["resumen"]


def test_year_period_detects_structural_transformation_message():
    historial = [
        _row("2025-02-01T00:00:00", 92.0, 34.0, 31.0),
        _row("2025-08-01T00:00:00", 86.0, 30.0, 35.0),
        _row("2026-02-01T00:00:00", 82.0, 28.0, 37.5),
    ]

    result = evaluar_progreso(objetivo="perdida_grasa", periodo="anio", historial=historial)
    assert result["periodo"] == "anio"
    assert "Transformación anual significativa" in result["resumen"]


def test_uses_closest_available_range_when_period_data_is_insufficient():
    historial = [
        _row("2025-01-01T00:00:00", 78.0, 22.0, 43.0),
        _row("2025-06-01T00:00:00", 77.0, 21.0, 44.0),
        _row("2026-02-01T00:00:00", 76.0, 20.0, 45.0),
    ]

    result = evaluar_progreso(objetivo="mantenimiento", periodo="semana", historial=historial)
    assert any("rango disponible más cercano" in warning for warning in result["advertencias"])
