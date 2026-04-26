"""Tests for Trello card #10 — avg_kcal_per_training_session.

The Gemini routine prompt explicitly forbids generating per-session calorie
estimates ("calorie calculations are handled server-side using MET formulas").
Until card #10, `diet_service` was still trying to read those fields, so the
training-day diet always added 0 extra kcal. These tests pin the contract:

  - The helper is deterministic given weight + duration + activity.
  - New routines persist the field at creation/edit.
  - Existing routines backfill on first GET.
  - `diet_service` reads the persisted field, not the deprecated source.
"""

from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import User, UserRoutine
from app.services.routine_service import RoutineService


# ── Test DB session helper (reuses the test DB the `client` fixture builds) ──

@pytest.fixture
def db_session(client: TestClient):
    """Yield a SQLAlchemy session against the test DB.

    Depends on `client` so the schema is created and exercise activities are
    seeded before the test runs.
    """
    from app.tests.conftest import TestingSessionLocal

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def _make_routine_data(num_sessions: int, duration_each: int = 60) -> dict[str, Any]:
    """Build a minimal routine_data dict with `num_sessions` sessions.

    Each session has 5 dummy exercises and the given duration. Mirrors the
    shape produced by Gemini per the prompt schema.
    """
    return {
        "title": "Test routine",
        "sessions": [
            {
                "id": f"session_{i}",
                "title": f"Session {i}",
                "session_duration_minutes": duration_each,
                "exercises": [
                    {"id": f"ex_{i}_{j}", "name": f"Exercise {j}"}
                    for j in range(5)
                ],
            }
            for i in range(num_sessions)
        ],
    }


# ── 1. Helper unit tests ──────────────────────────────────────────────────────

def test_compute_avg_kcal_returns_zero_when_weight_missing(db_session: Session):
    """No weight → no calories. Cannot estimate without it."""
    routine_data = _make_routine_data(num_sessions=3)
    avg = RoutineService._compute_avg_kcal_per_training_session(
        db_session, routine_data=routine_data, weight_kg=0
    )
    assert avg == 0.0


def test_compute_avg_kcal_returns_zero_when_no_sessions(db_session: Session):
    """Empty routine → zero. Avoid div-by-zero."""
    avg = RoutineService._compute_avg_kcal_per_training_session(
        db_session, routine_data={"sessions": []}, weight_kg=70
    )
    assert avg == 0.0


def test_compute_avg_kcal_single_session_60min_70kg(db_session: Session):
    """Pin the formula. WorkoutService.calculate_block_metrics for `medium`
    intensity uses the (met_medium, met_high) window — for fuerza_general
    that's (5.0, 6.0) → met_est = 5.5. So 5.5 × 70 × 1h = 385 kcal.
    """
    routine_data = _make_routine_data(num_sessions=1, duration_each=60)
    avg = RoutineService._compute_avg_kcal_per_training_session(
        db_session, routine_data=routine_data, weight_kg=70
    )
    assert 384.0 <= avg <= 386.0


def test_compute_avg_kcal_scales_with_weight(db_session: Session):
    """Heavier user → more calories per session (linear in weight)."""
    routine_data = _make_routine_data(num_sessions=1, duration_each=60)
    avg_50 = RoutineService._compute_avg_kcal_per_training_session(
        db_session, routine_data=routine_data, weight_kg=50
    )
    avg_100 = RoutineService._compute_avg_kcal_per_training_session(
        db_session, routine_data=routine_data, weight_kg=100
    )
    # Doubling weight should roughly double the kcal estimate.
    assert avg_100 == pytest.approx(avg_50 * 2, rel=0.01)


def test_compute_avg_kcal_averages_across_sessions(db_session: Session):
    """3 identical sessions → avg equals single-session value."""
    one = _make_routine_data(num_sessions=1, duration_each=60)
    three = _make_routine_data(num_sessions=3, duration_each=60)
    avg_one = RoutineService._compute_avg_kcal_per_training_session(
        db_session, routine_data=one, weight_kg=70
    )
    avg_three = RoutineService._compute_avg_kcal_per_training_session(
        db_session, routine_data=three, weight_kg=70
    )
    assert avg_three == pytest.approx(avg_one, abs=0.5)


def test_compute_avg_kcal_handles_mixed_durations(db_session: Session):
    """Mix of 30-min and 90-min sessions — the average should reflect both."""
    routine_data = {
        "title": "Mixed",
        "sessions": [
            {"id": "s1", "session_duration_minutes": 30, "exercises": []},
            {"id": "s2", "session_duration_minutes": 90, "exercises": []},
        ],
    }
    avg = RoutineService._compute_avg_kcal_per_training_session(
        db_session, routine_data=routine_data, weight_kg=70
    )
    # 30min: 5.5 × 70 × 0.5 = 192.5 ; 90min: 5.5 × 70 × 1.5 = 577.5 ; avg = 385
    assert 384.0 <= avg <= 386.0


# ── 2. Persistence tests ──────────────────────────────────────────────────────

def test_set_record_ready_injects_avg_kcal_into_routine_data(
    db_session: Session, client: TestClient, test_user_data: dict[str, Any]
):
    """When generate/edit completes, raw_data should gain the field
    before being written to UserRoutine.routine_data."""
    # Register a real user (60 kg via test_user_data override below)
    user_data = {**test_user_data, "weight": 60.0}
    client.post("/auth/register", json=user_data)

    user = db_session.query(User).filter(User.email == user_data["email"]).first()
    assert user is not None

    routine = UserRoutine(
        user_id=user.id,
        source_filename="ai_test",
        source_type="ai_text",
        status="processing",
    )
    db_session.add(routine)
    db_session.commit()
    db_session.refresh(routine)

    raw_data = _make_routine_data(num_sessions=2, duration_each=60)
    RoutineService._set_record_ready(routine, raw_data=raw_data, html="<p>x</p>")
    db_session.commit()

    db_session.refresh(routine)
    persisted: dict[str, Any] = routine.routine_data or {}
    assert "avg_kcal_per_training_session" in persisted
    # 60 kg × 5.5 MET × 1h = 330 kcal
    assert 329.0 <= persisted["avg_kcal_per_training_session"] <= 331.0


def test_get_active_routine_backfills_missing_avg_kcal(
    db_session: Session, client: TestClient, test_user_data: dict[str, Any]
):
    """A routine created before card #10 has no avg_kcal_per_training_session.
    First GET after the upgrade should compute and persist it."""
    user_data = {**test_user_data, "weight": 80.0}
    client.post("/auth/register", json=user_data)
    user = db_session.query(User).filter(User.email == user_data["email"]).first()
    assert user is not None

    legacy_routine_data = _make_routine_data(num_sessions=1, duration_each=60)
    # Simulate a pre-card-#10 routine: no avg_kcal field present.
    assert "avg_kcal_per_training_session" not in legacy_routine_data

    routine = UserRoutine(
        user_id=user.id,
        source_filename="legacy",
        source_type="ai_text",
        status="ready",
        routine_data=legacy_routine_data,
    )
    db_session.add(routine)
    db_session.commit()

    # First GET: should backfill.
    fetched = RoutineService.get_active_routine(db_session, user_id=user.id)
    persisted: dict[str, Any] = fetched.routine_data or {}
    assert "avg_kcal_per_training_session" in persisted
    # 80 kg × 5.5 MET × 1h = 440 kcal
    assert 439.0 <= persisted["avg_kcal_per_training_session"] <= 441.0

    # Second GET: should NOT recompute (idempotent).
    persisted_avg_first = persisted["avg_kcal_per_training_session"]
    fetched_again = RoutineService.get_active_routine(db_session, user_id=user.id)
    persisted_again: dict[str, Any] = fetched_again.routine_data or {}
    assert persisted_again["avg_kcal_per_training_session"] == persisted_avg_first


# ── 3. Diet service integration ───────────────────────────────────────────────

def test_diet_prompt_reads_persisted_avg_kcal_not_deprecated_field():
    """The diet prompt builder reads `avg_kcal_per_training_session` from the
    routine_data top-level. The old per-session `estimated_calories_per_session`
    must NOT influence the result (Gemini was asked not to generate it)."""
    from app.services.diet_service import _build_diet_generation_prompt

    routine_data = {
        "sessions": [
            # Old field, should be ignored:
            {"id": "s1", "title": "Push", "estimated_calories_per_session": 999},
            {"id": "s2", "title": "Pull", "estimated_calories_per_session": 999},
        ],
        # Server-computed value, what the diet should use:
        "avg_kcal_per_training_session": 287.0,
    }

    prompt = _build_diet_generation_prompt(
        intake={"meals_count": 4, "training_days": ["Lunes", "Miércoles"]},
        free_text="",
        user_bio={
            "age": 30,
            "gender": "female",
            "weight_kg": 65,
            "height_cm": 170,
            "activity_level": 1.5,
            "target_calories": 2000,
        },
        routine_data=routine_data,
    )
    # The prompt cites the persisted server value (rounded), not 999.
    assert "287" in prompt
    assert "999" not in prompt
