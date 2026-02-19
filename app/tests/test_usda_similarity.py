from app.services.usda_service import RankedUSDAResult, _select_best_candidate


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
