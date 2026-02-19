from app.services.usda_service import (
    RankedUSDAResult,
    _build_query_candidates,
    _preparation_alignment_bonus,
    _select_best_candidate,
    rank_usda_results,
)


def test_select_best_candidate_accepts_high_50s_similarity_for_generic_queries() -> None:
    ranked = [
        RankedUSDAResult(
            food={"fdcId": 1},
            description="Fish broth",
            category="Foundation",
            similarity_score=57.14,
            weighted_score=67.14,
        )
    ]

    best = _select_best_candidate("fish", ranked)
    assert best.description == "Fish broth"


def test_preparation_alignment_bonus_prioritizes_fried_when_query_is_fried() -> None:
    fried_bonus = _preparation_alignment_bonus("fried chicken", "Chicken, broilers or fryers, meat and skin, fried")
    raw_penalty = _preparation_alignment_bonus("fried chicken", "Chicken, broilers or fryers, meat only, raw")

    assert fried_bonus > 0
    assert raw_penalty < 0


def test_rank_usda_results_defaults_brown_rice_to_cooked_when_state_missing() -> None:
    foods = [
        {
            "description": "Rice, brown, long-grain, raw",
            "dataType": "Foundation",
            "foodNutrients": [],
        },
        {
            "description": "Rice, brown, long-grain, cooked",
            "dataType": "Foundation",
            "foodNutrients": [],
        },
    ]

    ranked = rank_usda_results("brown rice", foods)

    assert ranked[0].description == "Rice, brown, long-grain, cooked"


def test_rank_usda_results_penalizes_meatless_for_animal_query() -> None:
    foods = [
        {
            "description": "Chicken, meatless, breaded, fried",
            "dataType": "Foundation",
            "foodNutrients": [],
        },
        {
            "description": "Chicken, broilers or fryers, meat and skin, fried",
            "dataType": "Foundation",
            "foodNutrients": [],
        },
    ]

    ranked = rank_usda_results("fried chicken", foods)

    assert ranked[0].description == "Chicken, broilers or fryers, meat and skin, fried"


def test_build_query_candidates_adds_brewed_variant_for_plain_coffee() -> None:
    candidates = _build_query_candidates("coffee")

    assert candidates[0] == "coffee brewed"
    assert "coffee" in candidates


def test_build_query_candidates_adds_fluid_variant_for_plain_milk() -> None:
    candidates = _build_query_candidates("milk")

    assert candidates[0] == "milk fluid"
    assert "milk" in candidates
