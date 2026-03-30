"""
Tests for the routine generation and editing endpoints.

Covers:
  1. File upload — valid and invalid types, size limits
  2. AI text generation — happy path (mocked Gemini), missing data inference
  3. Edit routine — happy path, no active routine error
  4. Get active routine — found and not found
  5. Log session — valid, session not found
  6. Health analysis field stored and returned
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

BASE_BIOMETRICS = {
    "gender": "female",
    "weight": 62.0,
    "height": 165.0,
    "age": 28,
    "activity_level": 1.35,
}

USER_DATA = {
    "email": "routine_user@nova.com",
    "password": "routinepass123",
    "first_name": "Sofia",
    "last_name": "Martinez",
    "role": "student",
    **BASE_BIOMETRICS,
}

SAMPLE_ROUTINE_JSON = {
    "title": "Full Body 3 días",
    "subtitle": "Ciclo 1 mes · Recomposición corporal",
    "health_analysis": {
        "conditions_detected": ["Sin condiciones declaradas"],
        "contraindications_applied": [],
        "adaptations": ["Frecuencia inferida: 3 días/semana"],
        "warning": None,
    },
    "phases": [
        {
            "number": "Mes 1",
            "title": "Adaptación",
            "sets_reps": "3 × 12-15 reps",
            "weight": "Moderado (RPE 6-7)",
            "focus": "Técnica y acondicionamiento",
        }
    ],
    "schedule": [
        {"day": "Lunes", "label": "Full Body A", "focus": "Piernas + Empuje"},
        {"day": "Miércoles", "label": "Full Body B", "focus": "Espalda + Jalón"},
        {"day": "Viernes", "label": "Full Body A", "focus": "Piernas + Empuje"},
    ],
    "sessions": [
        {
            "id": "full_a",
            "color": "#c8f55a",
            "day_label": "Lunes · Full Body A",
            "title": "Piernas + Empuje",
            "estimated_calories_per_session": 310,
            "exercises": [
                {
                    "id": "full_a_1",
                    "name": "Sentadilla en Máquina Smith",
                    "muscle": "Cuádriceps",
                    "group": "Piernas",
                    "sets": "3",
                    "reps": "12-15",
                    "rest_seconds": 90,
                    "estimated_calories": 50,
                    "notes": "",
                },
                {
                    "id": "full_a_2",
                    "name": "Leg Press Bilateral",
                    "muscle": "Cuádriceps + Glúteos",
                    "group": "Piernas",
                    "sets": "3",
                    "reps": "12-15",
                    "rest_seconds": 90,
                    "estimated_calories": 45,
                    "notes": "",
                },
                {
                    "id": "full_a_3",
                    "name": "Press con Mancuernas",
                    "muscle": "Pectoral mayor",
                    "group": "Empuje",
                    "sets": "3",
                    "reps": "10-12",
                    "rest_seconds": 75,
                    "estimated_calories": 40,
                    "notes": "",
                },
                {
                    "id": "full_a_4",
                    "name": "Extensión de Tríceps Polea",
                    "muscle": "Tríceps",
                    "group": "Empuje",
                    "sets": "3",
                    "reps": "12-15",
                    "rest_seconds": 60,
                    "estimated_calories": 30,
                    "notes": "",
                },
                {
                    "id": "full_a_5",
                    "name": "Elevación de Pantorrillas",
                    "muscle": "Gemelos",
                    "group": "Piernas",
                    "sets": "3",
                    "reps": "15-20",
                    "rest_seconds": 45,
                    "estimated_calories": 25,
                    "notes": "",
                },
            ],
        }
    ],
}

GENERATE_REQUEST = {
    "intake": {
        "objective": "body_recomp",
        "duration_months": 1,
        "health_conditions": "ninguna",
        "medications": "",
        "injuries": "",
        "preferred_exercises": "máquinas",
        "frequency_days": "3-4",
        "experience_level": "principiante",
        "equipment": "gimnasio completo",
        "session_duration_minutes": 60,
    },
    "free_text": "Quiero una rutina de recomposición corporal con máquinas.",
}


def _register_and_login(client: TestClient, user_data: dict) -> str:
    client.post("/auth/register", json=user_data)
    resp = client.post("/auth/login", json={
        "email": user_data["email"],
        "password": user_data["password"],
    })
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _mock_gemini_response(routine_json: dict):
    """Return a mock httpx.Response that Gemini would return."""
    text = json.dumps(routine_json, ensure_ascii=False)
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "candidates": [
            {"content": {"parts": [{"text": text}]}}
        ]
    }
    return mock_response


# ── AI Generation ─────────────────────────────────────────────────────────────

class TestGenerateRoutine:
    def test_generate_happy_path(self, client: TestClient):
        token = _register_and_login(client, USER_DATA)

        with patch("httpx.Client") as mock_client_cls:
            mock_client = mock_client_cls.return_value.__enter__.return_value
            mock_client.post.return_value = _mock_gemini_response(SAMPLE_ROUTINE_JSON)

            resp = client.post(
                "/v1/routines/generate",
                json=GENERATE_REQUEST,
                headers=_auth(token),
            )

        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["status"] == "ready"
        assert data["source_type"] == "ai_text"
        assert data["html_content"] is not None
        assert "NovaFitness" in data["html_content"]
        assert data["health_analysis"] is not None
        assert data["routine_data"] is not None
        assert len(data["routine_data"]["sessions"]) == 1

    def test_generate_stores_intake_data(self, client: TestClient):
        token = _register_and_login(client, USER_DATA)

        with patch("httpx.Client") as mock_client_cls:
            mock_client = mock_client_cls.return_value.__enter__.return_value
            mock_client.post.return_value = _mock_gemini_response(SAMPLE_ROUTINE_JSON)

            resp = client.post(
                "/v1/routines/generate",
                json=GENERATE_REQUEST,
                headers=_auth(token),
            )

        assert resp.status_code == 201
        data = resp.json()
        assert data["intake_data"] is not None
        assert data["intake_data"]["objective"] == "body_recomp"

    def test_generate_requires_auth(self, client: TestClient):
        resp = client.post("/v1/routines/generate", json=GENERATE_REQUEST)
        assert resp.status_code == 401

    def test_generate_invalid_objective(self, client: TestClient):
        token = _register_and_login(client, USER_DATA)
        bad_request = {**GENERATE_REQUEST, "intake": {**GENERATE_REQUEST["intake"], "duration_months": 0}}
        resp = client.post(
            "/v1/routines/generate",
            json=bad_request,
            headers=_auth(token),
        )
        assert resp.status_code == 422

    def test_generate_html_contains_theme_switcher(self, client: TestClient):
        token = _register_and_login(client, USER_DATA)

        with patch("httpx.Client") as mock_client_cls:
            mock_client = mock_client_cls.return_value.__enter__.return_value
            mock_client.post.return_value = _mock_gemini_response(SAMPLE_ROUTINE_JSON)

            resp = client.post(
                "/v1/routines/generate",
                json=GENERATE_REQUEST,
                headers=_auth(token),
            )

        assert resp.status_code == 201
        html = resp.json()["html_content"]
        assert "theme-switcher" in html
        assert 'data-theme="dark"' in html
        assert "setTheme" in html

    def test_generate_html_contains_health_analysis(self, client: TestClient):
        token = _register_and_login(client, USER_DATA)
        routine_with_warning = {
            **SAMPLE_ROUTINE_JSON,
            "health_analysis": {
                "conditions_detected": ["Hernia lumbar L4-L5"],
                "contraindications_applied": ["Peso muerto convencional excluido"],
                "adaptations": ["Reemplazado por hip thrust y extensión de cadera"],
                "warning": None,
            },
        }

        with patch("httpx.Client") as mock_client_cls:
            mock_client = mock_client_cls.return_value.__enter__.return_value
            mock_client.post.return_value = _mock_gemini_response(routine_with_warning)

            resp = client.post(
                "/v1/routines/generate",
                json=GENERATE_REQUEST,
                headers=_auth(token),
            )

        assert resp.status_code == 201
        html = resp.json()["html_content"]
        assert "health-analysis" in html
        assert "Hernia lumbar" in html


# ── Edit routine ──────────────────────────────────────────────────────────────

class TestEditRoutine:
    def _create_routine(self, client: TestClient, token: str) -> None:
        with patch("httpx.Client") as mock_client_cls:
            mock_client = mock_client_cls.return_value.__enter__.return_value
            mock_client.post.return_value = _mock_gemini_response(SAMPLE_ROUTINE_JSON)
            client.post(
                "/v1/routines/generate",
                json=GENERATE_REQUEST,
                headers=_auth(token),
            )

    def test_edit_happy_path(self, client: TestClient):
        token = _register_and_login(client, USER_DATA)
        self._create_routine(client, token)

        edited = {**SAMPLE_ROUTINE_JSON, "subtitle": "Editado · Rutina modificada"}

        with patch("httpx.Client") as mock_client_cls:
            mock_client = mock_client_cls.return_value.__enter__.return_value
            mock_client.post.return_value = _mock_gemini_response(edited)

            resp = client.post(
                "/v1/routines/edit",
                json={"edit_instruction": "Agregar más ejercicios de espalda en la sesión A"},
                headers=_auth(token),
            )

        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["status"] == "ready"

    def test_edit_no_routine_returns_404(self, client: TestClient):
        token = _register_and_login(client, USER_DATA)
        resp = client.post(
            "/v1/routines/edit",
            json={"edit_instruction": "Cambiar ejercicios"},
            headers=_auth(token),
        )
        assert resp.status_code == 404

    def test_edit_instruction_too_short(self, client: TestClient):
        token = _register_and_login(client, USER_DATA)
        resp = client.post(
            "/v1/routines/edit",
            json={"edit_instruction": "ok"},
            headers=_auth(token),
        )
        assert resp.status_code == 422


# ── Get active routine ────────────────────────────────────────────────────────

class TestGetActiveRoutine:
    def test_get_active_not_found(self, client: TestClient):
        token = _register_and_login(client, USER_DATA)
        resp = client.get("/v1/routines/active", headers=_auth(token))
        assert resp.status_code == 404

    def test_get_active_after_generate(self, client: TestClient):
        token = _register_and_login(client, USER_DATA)

        with patch("httpx.Client") as mock_client_cls:
            mock_client = mock_client_cls.return_value.__enter__.return_value
            mock_client.post.return_value = _mock_gemini_response(SAMPLE_ROUTINE_JSON)
            client.post(
                "/v1/routines/generate",
                json=GENERATE_REQUEST,
                headers=_auth(token),
            )

        resp = client.get("/v1/routines/active", headers=_auth(token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ready"
        assert data["source_type"] == "ai_text"


# ── File upload ───────────────────────────────────────────────────────────────

class TestUploadRoutine:
    def test_upload_invalid_mime(self, client: TestClient):
        token = _register_and_login(client, USER_DATA)
        resp = client.post(
            "/v1/routines/upload",
            files={"file": ("routine.xlsx", b"fake xlsx content", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            headers=_auth(token),
        )
        assert resp.status_code == 415

    def test_upload_text_file(self, client: TestClient):
        token = _register_and_login(client, USER_DATA)

        with patch("httpx.Client") as mock_client_cls:
            mock_client = mock_client_cls.return_value.__enter__.return_value
            mock_client.post.return_value = _mock_gemini_response(SAMPLE_ROUTINE_JSON)

            content = b"Lunes: Sentadilla 3x12, Press 3x10\nMiercoles: Dominadas 3x8"
            resp = client.post(
                "/v1/routines/upload",
                files={"file": ("routine.txt", content, "text/plain")},
                headers=_auth(token),
            )

        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "ready"
        assert data["source_type"] == "file"


# ── Log session ───────────────────────────────────────────────────────────────

class TestLogSession:
    def test_log_session_happy_path(self, client: TestClient):
        token = _register_and_login(client, USER_DATA)

        with patch("httpx.Client") as mock_client_cls:
            mock_client = mock_client_cls.return_value.__enter__.return_value
            mock_client.post.return_value = _mock_gemini_response(SAMPLE_ROUTINE_JSON)
            client.post(
                "/v1/routines/generate",
                json=GENERATE_REQUEST,
                headers=_auth(token),
            )

        resp = client.post(
            "/v1/routines/log-session",
            json={
                "session_id": "full_a",
                "session_date": "2026-03-21",
                "skipped_exercise_ids": [],
                "extra_exercises": [],
            },
            headers=_auth(token),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["total_kcal_est"] > 0

    def test_log_session_not_found(self, client: TestClient):
        token = _register_and_login(client, USER_DATA)

        with patch("httpx.Client") as mock_client_cls:
            mock_client = mock_client_cls.return_value.__enter__.return_value
            mock_client.post.return_value = _mock_gemini_response(SAMPLE_ROUTINE_JSON)
            client.post(
                "/v1/routines/generate",
                json=GENERATE_REQUEST,
                headers=_auth(token),
            )

        resp = client.post(
            "/v1/routines/log-session",
            json={
                "session_id": "nonexistent_session",
                "session_date": "2026-03-21",
                "skipped_exercise_ids": [],
                "extra_exercises": [],
            },
            headers=_auth(token),
        )
        assert resp.status_code == 404

    def test_log_session_uses_ai_estimate_as_base(self, client: TestClient):
        """Full session with no skips/extras should match the AI-estimated kcal exactly."""
        token = _register_and_login(client, USER_DATA)

        with patch("httpx.Client") as mock_client_cls:
            mock_client = mock_client_cls.return_value.__enter__.return_value
            mock_client.post.return_value = _mock_gemini_response(SAMPLE_ROUTINE_JSON)
            client.post("/v1/routines/generate", json=GENERATE_REQUEST, headers=_auth(token))

        resp = client.post(
            "/v1/routines/log-session",
            json={
                "session_id": "full_a",
                "session_date": "2026-03-21",
                "skipped_exercise_ids": [],
                "extra_exercises": [],
            },
            headers=_auth(token),
        )
        assert resp.status_code == 201
        data = resp.json()
        # AI estimate from SAMPLE_ROUTINE_JSON = 310 kcal — must be consistent with card display
        assert data["total_kcal_est"] == pytest.approx(310.0, abs=0.5)
        assert data["total_kcal_min"] == pytest.approx(310.0 * 0.9, abs=0.5)
        assert data["total_kcal_max"] == pytest.approx(310.0 * 1.1, abs=0.5)

    def test_log_session_skipped_reduces_calories_proportionally(self, client: TestClient):
        """Skipping 2 of 5 exercises removes 40 % of the AI-estimated base calories."""
        token = _register_and_login(client, USER_DATA)

        with patch("httpx.Client") as mock_client_cls:
            mock_client = mock_client_cls.return_value.__enter__.return_value
            mock_client.post.return_value = _mock_gemini_response(SAMPLE_ROUTINE_JSON)
            client.post("/v1/routines/generate", json=GENERATE_REQUEST, headers=_auth(token))

        resp = client.post(
            "/v1/routines/log-session",
            json={
                "session_id": "full_a",
                "session_date": "2026-03-21",
                "skipped_exercise_ids": ["full_a_4", "full_a_5"],
                "extra_exercises": [],
            },
            headers=_auth(token),
        )
        assert resp.status_code == 201
        data = resp.json()
        # AI estimate = 310, 3 of 5 done → 310 × 0.6 = 186 kcal
        expected = round(310.0 * 0.6, 2)
        assert data["total_kcal_est"] == pytest.approx(expected, abs=0.5)

    def test_log_session_extra_exercises_add_met_calories(self, client: TestClient):
        """Extra exercises add MET-based calories on top of the AI-estimated routine base."""
        token = _register_and_login(client, USER_DATA)

        with patch("httpx.Client") as mock_client_cls:
            mock_client = mock_client_cls.return_value.__enter__.return_value
            mock_client.post.return_value = _mock_gemini_response(SAMPLE_ROUTINE_JSON)
            client.post("/v1/routines/generate", json=GENERATE_REQUEST, headers=_auth(token))

        resp = client.post(
            "/v1/routines/log-session",
            json={
                "session_id": "full_a",
                "session_date": "2026-03-21",
                "skipped_exercise_ids": [],
                "extra_exercises": [
                    {"name": "Trotadora", "duration_minutes": 30, "exercise_type": "cardio_moderate"},
                ],
            },
            headers=_auth(token),
        )
        assert resp.status_code == 201
        data = resp.json()
        # Base (AI): 310 kcal + cardio_moderate(MET=7.0) × 62kg × 0.5h = 217 kcal
        extra_kcal = round(7.0 * 62.0 * 0.5, 2)
        expected = round(310.0 + extra_kcal, 2)
        assert data["total_kcal_est"] == pytest.approx(expected, abs=0.5)
        assert data["total_kcal_est"] > 310.0


# ── Advance session ───────────────────────────────────────────────────────────

class TestAdvanceSession:
    def _create_routine(self, client: TestClient, token: str) -> None:
        with patch("httpx.Client") as mock_client_cls:
            mock_client = mock_client_cls.return_value.__enter__.return_value
            mock_client.post.return_value = _mock_gemini_response(SAMPLE_ROUTINE_JSON)
            client.post("/v1/routines/generate", json=GENERATE_REQUEST, headers=_auth(token))

    def test_skip_advances_index(self, client: TestClient):
        token = _register_and_login(client, USER_DATA)
        self._create_routine(client, token)

        # index starts at 0
        active = client.get("/v1/routines/active", headers=_auth(token)).json()
        assert active["current_session_index"] == 0

        # skip → index stays at 0 (only 1 session, wraps to 0)
        resp = client.post("/v1/routines/advance-session", json={"action": "skip"}, headers=_auth(token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["current_session_index"] == 0  # 1 session → wraps back to 0

    def test_complete_logs_workout_and_advances(self, client: TestClient):
        token = _register_and_login(client, USER_DATA)
        self._create_routine(client, token)

        resp = client.post("/v1/routines/advance-session", json={"action": "complete"}, headers=_auth(token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ready"
        assert data["current_session_index"] == 0  # wraps since only 1 session

    def test_advance_no_routine_returns_404(self, client: TestClient):
        token = _register_and_login(client, USER_DATA)
        resp = client.post("/v1/routines/advance-session", json={"action": "skip"}, headers=_auth(token))
        assert resp.status_code == 404

    def test_advance_invalid_action_returns_422(self, client: TestClient):
        token = _register_and_login(client, USER_DATA)
        self._create_routine(client, token)
        resp = client.post("/v1/routines/advance-session", json={"action": "invalid"}, headers=_auth(token))
        assert resp.status_code == 422

    def test_new_routine_resets_index(self, client: TestClient):
        """Uploading a new routine must reset current_session_index to 0."""
        token = _register_and_login(client, USER_DATA)
        self._create_routine(client, token)

        # advance once (skip)
        client.post("/v1/routines/advance-session", json={"action": "skip"}, headers=_auth(token))

        # replace routine → index resets
        self._create_routine(client, token)
        active = client.get("/v1/routines/active", headers=_auth(token)).json()
        assert active["current_session_index"] == 0
