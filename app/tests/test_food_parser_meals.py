from app.services.food_parser import parse_food_input, split_text_by_meal_type


def test_split_text_by_meal_type_detects_lunch_and_dinner() -> None:
    text = "almorcé pollo con arroz y luego cené pescado con ensalada"
    sections = split_text_by_meal_type(text)

    assert len(sections) == 2
    assert sections[0][0] == "lunch"
    assert "pollo" in sections[0][1]
    assert sections[1][0] == "dinner"
    assert "pescado" in sections[1][1]


def test_split_text_by_meal_type_fallback_single_meal() -> None:
    text = "pollo 100 gramos y arroz 200 gramos"
    sections = split_text_by_meal_type(text)

    assert sections == [("meal", text)]


def test_split_text_by_meal_type_temporal_words_create_two_meals() -> None:
    text = "comí pollo con arroz y después comí yogurt"
    sections = split_text_by_meal_type(text)

    assert len(sections) == 2
    assert sections[0][0] == "meal"
    assert "pollo" in sections[0][1]
    assert sections[1][0] == "meal"
    assert "yogurt" in sections[1][1]


def test_split_text_by_meal_type_luego_de_postre_stays_same_meal() -> None:
    text = "comí pollo con arroz y luego de postre helado"
    sections = split_text_by_meal_type(text)

    assert len(sections) == 1
    assert sections[0][0] == "meal"
    assert "postre" in sections[0][1].lower()


def test_parse_food_input_accepts_nested_meals_shape(monkeypatch) -> None:
    def fake_parse_food_with_gemini(_text: str):
        return {
            "meals": [
                {
                    "meal_type": "breakfast",
                    "items": [
                        {"name": "egg", "quantity": 2, "unit": "serving"},
                        {"name": "toast", "quantity": 1, "unit": "serving"},
                    ],
                },
                {
                    "meal_type": "lunch",
                    "items": [
                        {"name": "fish", "quantity": 1, "unit": "serving"},
                        {"name": "baked potato", "quantity": 200, "unit": "grams"},
                    ],
                },
            ]
        }

    monkeypatch.setattr("app.services.food_parser.parse_food_with_gemini", fake_parse_food_with_gemini)

    items = parse_food_input(
        "Hoy desayuné 2 huevos con tostada y café con leche; luego almorcé pescado con papas al horno"
    )

    assert len(items) == 4
    assert items[0].name == "egg"
    assert items[1].name == "toast"
    assert items[2].name == "fish"
    assert items[3].name == "baked potato"
