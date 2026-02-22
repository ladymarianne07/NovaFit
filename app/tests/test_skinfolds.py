import pytest

from app.schemas.skinfold import SkinfoldCalculationRequest, Sex
from app.services.skinfold_service import SkinfoldService


def register_and_login(client):
    user_data = {
        "email": "skinfold@example.com",
        "password": "testpassword123",
        "first_name": "Skin",
        "last_name": "Fold",
        "gender": "male",
        "weight": 78.0,
        "height": 178.0,
        "age": 29,
        "activity_level": 1.5,
    }
    client.post("/auth/register", json=user_data)
    login = client.post("/auth/login", json={"email": user_data["email"], "password": user_data["password"]})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestSkinfoldFormulas:
    def test_jp7_formula_male_known_input(self):
        payload = SkinfoldCalculationRequest(
            sex=Sex.MALE,
            age_years=30,
            weight_kg=80.0,
            measurement_unit="mm",
            chest_mm=10,
            midaxillary_mm=10,
            triceps_mm=10,
            subscapular_mm=10,
            abdomen_mm=10,
            suprailiac_mm=10,
            thigh_mm=10,
        )

        result = SkinfoldService.calculate(payload)

        assert result["method"] == "Jackson-Pollock 7 + Siri"
        assert result["sum_of_skinfolds_mm"] == 70
        assert result["body_density"] == pytest.approx(1.0756, abs=0.0002)
        assert result["body_fat_percent"] == pytest.approx(10.2, abs=0.2)
        assert result["fat_free_mass_percent"] == pytest.approx(89.8, abs=0.2)
        assert result["fat_mass_kg"] == pytest.approx(8.2, abs=0.2)
        assert result["lean_mass_kg"] == pytest.approx(71.8, abs=0.2)

    def test_jp7_formula_female_known_input(self):
        payload = SkinfoldCalculationRequest(
            sex=Sex.FEMALE,
            age_years=28,
            weight_kg=62.0,
            measurement_unit="mm",
            chest_mm=14,
            midaxillary_mm=12,
            triceps_mm=18,
            subscapular_mm=14,
            abdomen_mm=20,
            suprailiac_mm=16,
            thigh_mm=24,
        )

        result = SkinfoldService.calculate(payload)

        assert result["method"] == "Jackson-Pollock 7 + Siri"
        assert result["sum_of_skinfolds_mm"] == 118
        assert result["body_density"] == pytest.approx(1.0458, abs=0.0004)
        assert result["body_fat_percent"] == pytest.approx(23.3, abs=0.4)
        assert result["fat_free_mass_percent"] == pytest.approx(76.7, abs=0.4)

    def test_jp3_fallback_when_partial_sites(self):
        payload = SkinfoldCalculationRequest(
            sex=Sex.MALE,
            age_years=31,
            measurement_unit="mm",
            chest_mm=12,
            abdomen_mm=20,
            thigh_mm=15,
        )

        result = SkinfoldService.calculate(payload)

        assert result["method"].startswith("Jackson-Pollock 3")
        assert any("fallback" in w.lower() for w in result["warnings"])


class TestSkinfoldAPI:
    def test_calculate_and_save_skinfolds_success(self, client):
        headers = register_and_login(client)

        response = client.post(
            "/users/me/skinfolds",
            headers=headers,
            json={
                "sex": "male",
                "age_years": 29,
                "weight_kg": 78,
                "measurement_unit": "mm",
                "chest_mm": 11,
                "midaxillary_mm": 9,
                "triceps_mm": 12,
                "subscapular_mm": 11,
                "abdomen_mm": 18,
                "suprailiac_mm": 14,
                "thigh_mm": 16,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["method"] == "Jackson-Pollock 7 + Siri"
        assert "measured_at" in data
        assert "body_fat_percent" in data

    def test_skinfold_history_returns_saved_items(self, client):
        headers = register_and_login(client)

        client.post(
            "/users/me/skinfolds",
            headers=headers,
            json={
                "sex": "male",
                "age_years": 29,
                "measurement_unit": "mm",
                "chest_mm": 11,
                "midaxillary_mm": 9,
                "triceps_mm": 12,
                "subscapular_mm": 11,
                "abdomen_mm": 18,
                "suprailiac_mm": 14,
                "thigh_mm": 16,
            },
        )

        history = client.get("/users/me/skinfolds", headers=headers)
        assert history.status_code == 200
        items = history.json()
        assert len(items) >= 1
        assert "id" in items[0]

    def test_ai_parse_skinfolds_success(self, client):
        headers = register_and_login(client)

        response = client.post(
            "/users/me/skinfolds/ai-parse",
            headers=headers,
            json={
                "text": "Pecho 11/12/10, axilar 9, triceps 12, subescapular 11, abdomen 18, suprailiaco 14, muslo 16",
            },
        )

        assert response.status_code == 200
        parsed = response.json()["parsed"]
        assert parsed["chest_mm"] == pytest.approx(11.0, abs=0.1)
        assert parsed["abdomen_mm"] == 18
