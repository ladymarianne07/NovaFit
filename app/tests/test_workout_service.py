from types import SimpleNamespace
from typing import Any, cast

import pytest

from app.core.custom_exceptions import WorkoutValidationError, WorkoutWeightRequiredError
from app.db.models import ExerciseActivity, WorkoutSession
from app.services.workout_service import WorkoutService


class TestWorkoutService:
    def test_normalize_intensity_maps_spanish_terms(self) -> None:
        assert WorkoutService.normalize_intensity("baja") == "low"
        assert WorkoutService.normalize_intensity("moderada") == "medium"
        assert WorkoutService.normalize_intensity("intensa") == "high"

    def test_calculate_block_metrics_medium_intensity(self) -> None:
        activity = cast(
            ExerciseActivity,
            SimpleNamespace(met_low=3.0, met_medium=5.0, met_high=7.0),
        )

        metrics = WorkoutService.calculate_block_metrics(
            activity=activity,
            duration_minutes=30,
            weight_kg=70.0,
            intensity_level="medium",
            correction_factor=1.0,
        )

        assert metrics.intensity_level == "medium"
        assert metrics.met_used_min == 5.0
        assert metrics.met_used_max == 7.0
        assert metrics.kcal_min == 175.0
        assert metrics.kcal_max == 245.0
        assert metrics.kcal_est == 210.0

    def test_calculate_block_metrics_requires_weight(self) -> None:
        activity = cast(
            ExerciseActivity,
            SimpleNamespace(met_low=3.0, met_medium=5.0, met_high=7.0),
        )

        with pytest.raises(WorkoutWeightRequiredError):
            WorkoutService.calculate_block_metrics(
                activity=activity,
                duration_minutes=20,
                weight_kg=None,
                intensity_level="low",
                correction_factor=1.0,
            )

    def test_calculate_block_metrics_validates_duration(self) -> None:
        activity = cast(
            ExerciseActivity,
            SimpleNamespace(met_low=3.0, met_medium=5.0, met_high=7.0),
        )

        with pytest.raises(WorkoutValidationError):
            WorkoutService.calculate_block_metrics(
                activity=activity,
                duration_minutes=0,
                weight_kg=70.0,
                intensity_level="low",
                correction_factor=1.0,
            )

    def test_recalculate_session_totals(self) -> None:
        block_1 = SimpleNamespace(kcal_min=100.0, kcal_max=140.0, kcal_est=120.0)
        block_2 = SimpleNamespace(kcal_min=50.0, kcal_max=80.0, kcal_est=65.0)
        session = cast(
            WorkoutSession,
            SimpleNamespace(
                blocks=[block_1, block_2],
                total_kcal_min=0.0,
                total_kcal_max=0.0,
                total_kcal_est=0.0,
            ),
        )

        total_min, total_max, total_est = WorkoutService.recalculate_session_totals(session)

        assert total_min == 150.0
        assert total_max == 220.0
        assert total_est == 185.0
        session_data = cast(Any, session)
        assert session_data.total_kcal_min == 150.0
        assert session_data.total_kcal_max == 220.0
        assert session_data.total_kcal_est == 185.0
