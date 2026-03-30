"""
End-to-end tests for the Personal Trainer module.

Flow covered:
  1. Register a trainer and a student
  2. Trainer generates an invite code
  3. Student accepts the invite → link created
  4. Trainer lists students → student appears
  5. Trainer views student full profile
  6. Trainer edits student biometrics → notification created for student
  7. Student edits own objective → notification created for trainer
  8. Both users retrieve their notifications
  9. Mark notifications as read
 10. Trainer unlinks student → student disappears from list
 11. Error cases: expired/used invite, wrong trainer, non-trainer actions
"""

import pytest
from fastapi.testclient import TestClient

# Re-use the shared client fixture from conftest.py — do NOT define a separate
# engine or dependency override here, as that would conflict with other test
# modules loaded in the same pytest session.


BASE_BIOMETRICS = {
    "gender": "male",
    "weight": 75.0,
    "height": 178.0,
    "age": 28,
    "activity_level": 1.5,
}

TRAINER_DATA = {
    "email": "trainer@nova.com",
    "password": "trainerpass123",
    "first_name": "Carlos",
    "last_name": "Gutierrez",
    "role": "trainer",
    **BASE_BIOMETRICS,
}

STUDENT_DATA = {
    "email": "student@nova.com",
    "password": "studentpass123",
    "first_name": "Ana",
    "last_name": "Lopez",
    "role": "student",
    **BASE_BIOMETRICS,
}


def _register_and_login(client: TestClient, user_data: dict) -> str:
    """Helper: register a user and return their Bearer token."""
    client.post("/auth/register", json=user_data)
    resp = client.post("/auth/login", json={
        "email": user_data["email"],
        "password": user_data["password"],
    })
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Tests ──────────────────────────────────────────────────────────────────────

class TestTrainerRegistration:
    def test_register_as_trainer_sets_role(self, client):
        resp = client.post("/auth/register", json=TRAINER_DATA)
        assert resp.status_code == 201
        assert resp.json()["role"] == "trainer"

    def test_register_as_student_sets_role(self, client):
        resp = client.post("/auth/register", json=STUDENT_DATA)
        assert resp.status_code == 201
        assert resp.json()["role"] == "student"

    def test_default_role_is_student(self, client):
        data = {**STUDENT_DATA, "email": "norol@nova.com"}
        data.pop("role", None)
        resp = client.post("/auth/register", json=data)
        assert resp.status_code == 201
        assert resp.json()["role"] == "student"


class TestInviteFlow:
    def test_trainer_generates_invite(self, client):
        token = _register_and_login(client, TRAINER_DATA)
        resp = client.post("/trainer/invite", headers=_auth(token))
        assert resp.status_code == 201
        data = resp.json()
        assert "code" in data
        assert len(data["code"]) == 8
        assert "expires_at" in data

    def test_student_cannot_generate_invite(self, client):
        token = _register_and_login(client, STUDENT_DATA)
        resp = client.post("/trainer/invite", headers=_auth(token))
        assert resp.status_code == 403

    def test_trainer_gets_current_invite(self, client):
        token = _register_and_login(client, TRAINER_DATA)
        client.post("/trainer/invite", headers=_auth(token))
        resp = client.get("/trainer/invite", headers=_auth(token))
        assert resp.status_code == 200
        assert "code" in resp.json()

    def test_no_invite_returns_404(self, client):
        token = _register_and_login(client, TRAINER_DATA)
        resp = client.get("/trainer/invite", headers=_auth(token))
        assert resp.status_code == 404


class TestStudentLinking:
    def _setup(self, client):
        trainer_token = _register_and_login(client, TRAINER_DATA)
        student_token = _register_and_login(client, STUDENT_DATA)
        invite_resp = client.post("/trainer/invite", headers=_auth(trainer_token))
        code = invite_resp.json()["code"]
        return trainer_token, student_token, code

    def test_student_accepts_invite(self, client):
        trainer_token, student_token, code = self._setup(client)
        resp = client.post("/invite/accept", json={"code": code}, headers=_auth(student_token))
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "active"

    def test_invite_cannot_be_used_twice(self, client):
        trainer_token, student_token, code = self._setup(client)
        client.post("/invite/accept", json={"code": code}, headers=_auth(student_token))
        # Second student tries to use the same code
        student2_data = {**STUDENT_DATA, "email": "student2@nova.com"}
        student2_token = _register_and_login(client, student2_data)
        resp = client.post("/invite/accept", json={"code": code}, headers=_auth(student2_token))
        assert resp.status_code == 409

    def test_invalid_code_returns_404(self, client):
        student_token = _register_and_login(client, STUDENT_DATA)
        resp = client.post("/invite/accept", json={"code": "XXXXXXXX"}, headers=_auth(student_token))
        assert resp.status_code == 404

    def test_student_already_linked_cannot_accept_another(self, client):
        trainer_token, student_token, code = self._setup(client)
        client.post("/invite/accept", json={"code": code}, headers=_auth(student_token))
        # Create a second trainer and invite
        trainer2_data = {**TRAINER_DATA, "email": "trainer2@nova.com"}
        trainer2_token = _register_and_login(client, trainer2_data)
        invite2 = client.post("/trainer/invite", headers=_auth(trainer2_token)).json()["code"]
        resp = client.post("/invite/accept", json={"code": invite2}, headers=_auth(student_token))
        assert resp.status_code == 409

    def test_accept_invite_notifies_trainer(self, client):
        trainer_token, student_token, code = self._setup(client)
        client.post("/invite/accept", json={"code": code}, headers=_auth(student_token))
        notifs = client.get("/notifications", headers=_auth(trainer_token)).json()
        assert notifs["unread_count"] >= 1
        types = [n["type"] for n in notifs["notifications"]]
        assert "invite_accepted" in types


class TestTrainerStudentView:
    def _linked_setup(self, client):
        trainer_token = _register_and_login(client, TRAINER_DATA)
        student_token = _register_and_login(client, STUDENT_DATA)
        code = client.post("/trainer/invite", headers=_auth(trainer_token)).json()["code"]
        client.post("/invite/accept", json={"code": code}, headers=_auth(student_token))
        return trainer_token, student_token

    def test_trainer_lists_students(self, client):
        trainer_token, _ = self._linked_setup(client)
        resp = client.get("/trainer/students", headers=_auth(trainer_token))
        assert resp.status_code == 200
        students = resp.json()
        assert len(students) == 1
        assert students[0]["email"] == STUDENT_DATA["email"]

    def test_trainer_gets_student_profile(self, client):
        trainer_token, _ = self._linked_setup(client)
        students = client.get("/trainer/students", headers=_auth(trainer_token)).json()
        student_id = students[0]["id"]
        resp = client.get(f"/trainer/students/{student_id}", headers=_auth(trainer_token))
        assert resp.status_code == 200
        assert resp.json()["email"] == STUDENT_DATA["email"]

    def test_trainer_cannot_view_unlinked_student(self, client):
        trainer_token = _register_and_login(client, TRAINER_DATA)
        # Register a student but don't link
        _register_and_login(client, STUDENT_DATA)
        resp = client.get("/trainer/students/9999", headers=_auth(trainer_token))
        assert resp.status_code == 404

    def test_student_list_is_empty_before_linking(self, client):
        trainer_token = _register_and_login(client, TRAINER_DATA)
        resp = client.get("/trainer/students", headers=_auth(trainer_token))
        assert resp.status_code == 200
        assert resp.json() == []


class TestTrainerEditsStudent:
    def _linked_setup(self, client):
        trainer_token = _register_and_login(client, TRAINER_DATA)
        student_token = _register_and_login(client, STUDENT_DATA)
        code = client.post("/trainer/invite", headers=_auth(trainer_token)).json()["code"]
        client.post("/invite/accept", json={"code": code}, headers=_auth(student_token))
        students = client.get("/trainer/students", headers=_auth(trainer_token)).json()
        student_id = students[0]["id"]
        return trainer_token, student_token, student_id

    def test_trainer_updates_student_biometrics(self, client):
        trainer_token, student_token, student_id = self._linked_setup(client)
        resp = client.put(
            f"/trainer/students/{student_id}/biometrics",
            json={"weight": 80.0, "height": 180.0, "age": 29, "gender": "male", "activity_level": 1.65},
            headers=_auth(trainer_token),
        )
        assert resp.status_code == 200
        assert resp.json()["weight"] == 80.0

    def test_trainer_edit_notifies_student(self, client):
        trainer_token, student_token, student_id = self._linked_setup(client)
        # Clear invite_accepted notification first by marking all read
        client.put("/notifications/read-all", headers=_auth(student_token))

        client.put(
            f"/trainer/students/{student_id}/biometrics",
            json={"weight": 80.0, "height": 180.0, "age": 29, "gender": "male", "activity_level": 1.65},
            headers=_auth(trainer_token),
        )
        notifs = client.get("/notifications", headers=_auth(student_token)).json()
        assert notifs["unread_count"] >= 1
        types = [n["type"] for n in notifs["notifications"]]
        assert "trainer_edited_biometrics" in types

    def test_trainer_updates_student_objective(self, client):
        trainer_token, _, student_id = self._linked_setup(client)
        resp = client.put(
            f"/trainer/students/{student_id}/objective",
            json={"objective": "fat_loss", "aggressiveness_level": 2},
            headers=_auth(trainer_token),
        )
        assert resp.status_code == 200
        assert resp.json()["objective"] == "fat_loss"


class TestStudentEditsNotifyTrainer:
    def _linked_setup(self, client):
        trainer_token = _register_and_login(client, TRAINER_DATA)
        student_token = _register_and_login(client, STUDENT_DATA)
        code = client.post("/trainer/invite", headers=_auth(trainer_token)).json()["code"]
        client.post("/invite/accept", json={"code": code}, headers=_auth(student_token))
        return trainer_token, student_token

    def test_student_biometric_edit_notifies_trainer(self, client):
        trainer_token, student_token = self._linked_setup(client)
        # Mark all current notifications as read
        client.put("/notifications/read-all", headers=_auth(trainer_token))

        client.put(
            "/users/me/biometrics",
            json={"weight": 72.0},
            headers=_auth(student_token),
        )
        notifs = client.get("/notifications", headers=_auth(trainer_token)).json()
        assert notifs["unread_count"] >= 1
        types = [n["type"] for n in notifs["notifications"]]
        assert "student_edited_biometrics" in types

    def test_student_objective_edit_notifies_trainer(self, client):
        trainer_token, student_token = self._linked_setup(client)
        client.put("/notifications/read-all", headers=_auth(trainer_token))

        client.put(
            "/users/me/objective",
            json={"objective": "muscle_gain", "aggressiveness_level": 1},
            headers=_auth(student_token),
        )
        notifs = client.get("/notifications", headers=_auth(trainer_token)).json()
        types = [n["type"] for n in notifs["notifications"]]
        assert "student_edited_objective" in types

    def test_student_without_trainer_edit_creates_no_notification(self, client):
        # Student with no trainer
        student_token = _register_and_login(client, STUDENT_DATA)
        client.put("/users/me/biometrics", json={"weight": 70.0}, headers=_auth(student_token))
        notifs = client.get("/notifications", headers=_auth(student_token)).json()
        # No notifications should be created (no trainer to notify)
        trainer_notif_types = [
            n["type"] for n in notifs["notifications"]
            if n["type"].startswith("student_edited")
        ]
        assert trainer_notif_types == []


class TestNotifications:
    def _linked_setup(self, client):
        trainer_token = _register_and_login(client, TRAINER_DATA)
        student_token = _register_and_login(client, STUDENT_DATA)
        code = client.post("/trainer/invite", headers=_auth(trainer_token)).json()["code"]
        client.post("/invite/accept", json={"code": code}, headers=_auth(student_token))
        return trainer_token, student_token

    def test_mark_single_notification_as_read(self, client):
        trainer_token, _ = self._linked_setup(client)
        notifs = client.get("/notifications", headers=_auth(trainer_token)).json()
        notif_id = notifs["notifications"][0]["id"]
        resp = client.put(f"/notifications/{notif_id}/read", headers=_auth(trainer_token))
        assert resp.status_code == 204
        updated = client.get("/notifications", headers=_auth(trainer_token)).json()
        read_notif = next(n for n in updated["notifications"] if n["id"] == notif_id)
        assert read_notif["is_read"] is True

    def test_mark_all_notifications_as_read(self, client):
        trainer_token, _ = self._linked_setup(client)
        resp = client.put("/notifications/read-all", headers=_auth(trainer_token))
        assert resp.status_code == 204
        updated = client.get("/notifications", headers=_auth(trainer_token)).json()
        assert updated["unread_count"] == 0

    def test_cannot_mark_another_users_notification(self, client):
        trainer_token, student_token = self._linked_setup(client)
        trainer_notifs = client.get("/notifications", headers=_auth(trainer_token)).json()
        notif_id = trainer_notifs["notifications"][0]["id"]
        # Student tries to mark trainer's notification
        resp = client.put(f"/notifications/{notif_id}/read", headers=_auth(student_token))
        assert resp.status_code == 404


class TestUnlinkStudent:
    def test_trainer_unlinks_student(self, client):
        trainer_token = _register_and_login(client, TRAINER_DATA)
        student_token = _register_and_login(client, STUDENT_DATA)
        code = client.post("/trainer/invite", headers=_auth(trainer_token)).json()["code"]
        client.post("/invite/accept", json={"code": code}, headers=_auth(student_token))

        students = client.get("/trainer/students", headers=_auth(trainer_token)).json()
        assert len(students) == 1
        student_id = students[0]["id"]

        resp = client.delete(f"/trainer/students/{student_id}", headers=_auth(trainer_token))
        assert resp.status_code == 204

        students_after = client.get("/trainer/students", headers=_auth(trainer_token)).json()
        assert len(students_after) == 0

    def test_cannot_unlink_already_unlinked(self, client):
        trainer_token = _register_and_login(client, TRAINER_DATA)
        student_token = _register_and_login(client, STUDENT_DATA)
        code = client.post("/trainer/invite", headers=_auth(trainer_token)).json()["code"]
        client.post("/invite/accept", json={"code": code}, headers=_auth(student_token))
        students = client.get("/trainer/students", headers=_auth(trainer_token)).json()
        student_id = students[0]["id"]

        client.delete(f"/trainer/students/{student_id}", headers=_auth(trainer_token))
        resp = client.delete(f"/trainer/students/{student_id}", headers=_auth(trainer_token))
        assert resp.status_code == 404
