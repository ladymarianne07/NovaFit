from app.services.food_parser import split_text_by_meal_type


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
