from app.services.ai_parser_service import (
    _build_model_candidates,
    _is_invalid_model_format_response,
    _normalize_model_name,
)


def test_normalize_model_name_handles_case_and_prefix() -> None:
    assert _normalize_model_name("gemini-2.5-FLASH") == "gemini-2.5-flash"
    assert _normalize_model_name("models/gemini-2.5-FLASH") == "gemini-2.5-flash"


def test_normalize_model_name_strips_operation_suffix() -> None:
    assert (
        _normalize_model_name("models/gemini-2.5-flash:generateContent")
        == "gemini-2.5-flash"
    )


def test_build_model_candidates_deduplicates_after_normalization() -> None:
    candidates = _build_model_candidates("GEMINI-2.5-FLASH")
    assert candidates[0] == "gemini-2.5-flash"
    assert len(candidates) == len(set(candidates))


def test_invalid_model_format_response_detection() -> None:
    body = '{"error":{"code":400,"message":"* GenerateContentRequest.model: unexpected model name format"}}'
    assert _is_invalid_model_format_response(400, body) is True
    assert _is_invalid_model_format_response(404, body) is False
