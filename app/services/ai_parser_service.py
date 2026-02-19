import json
import logging
from typing import Any
import re

import httpx

from ..config import settings


logger = logging.getLogger(__name__)

# Configure httpx logging to suppress sensitive information
logging.getLogger("httpx").setLevel(logging.WARNING)


def _sanitize_url_for_logging(url: str) -> str:
    """Remove API keys from URL before logging."""
    return re.sub(r'key=[^&\s]+', 'key=***REDACTED***', url)


GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

SYSTEM_PROMPT = (
    "You are a strict food parser for a fitness application.\n"
    "You only process food entries.\n"
    "You convert Spanish input into structured English JSON.\n"
    "You do not provide explanations.\n"
    "Extract all foods mentioned, even when the text includes multiple meals (breakfast/lunch/dinner/snacks).\n"
    "Ignore meal labels in the output and return only food items.\n"
    "If input is not food-related, return:\n"
    '{ "error": "invalid_domain" }\n'
    "If quantity is missing or unclear, return:\n"
    '{ "name": "english food name", "quantity": 1, "unit": "serving" }\n'
    "If input contains multiple foods, return:\n"
    '{ "items": [{"name": "english food name", "quantity": number, "unit": "grams" or "serving"}] }\n'
    "If the user gives a general food input with no explicit amount, infer one standard serving.\n"
    "Output must be valid JSON only.\n"
    "Format:\n"
    "{\n"
    '"name": "english food name",\n'
    '"quantity": number,\n'
    '"unit": "grams" or "serving"\n'
    "}\n"
    "No additional text."
)


class AIParserError(Exception):
    """Raised when Gemini parser fails or returns invalid response."""


def _extract_text_from_gemini_response(data: dict[str, Any]) -> str:
    candidates: Any = data.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise AIParserError("empty_ai_response")

    first_candidate = candidates[0]
    if not isinstance(first_candidate, dict):
        raise AIParserError("malformed_ai_response")

    content = first_candidate.get("content")
    if not isinstance(content, dict):
        raise AIParserError("malformed_ai_response")

    parts: Any = content.get("parts")
    if not isinstance(parts, list) or not parts:
        raise AIParserError("malformed_ai_response")

    first_part = parts[0]
    if not isinstance(first_part, dict):
        raise AIParserError("malformed_ai_response")

    text: Any = first_part.get("text")
    if not isinstance(text, str) or not text.strip():
        raise AIParserError("malformed_ai_response")

    return text.strip()


def _extract_json_candidate(raw_text: str) -> str:
    """Extract probable JSON segment from model text, tolerating wrappers/fences."""
    cleaned = raw_text.strip()

    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()

    if (cleaned.startswith("{") and cleaned.endswith("}")) or (
        cleaned.startswith("[") and cleaned.endswith("]")
    ):
        return cleaned

    first_obj = cleaned.find("{")
    first_arr = cleaned.find("[")
    starts = [idx for idx in (first_obj, first_arr) if idx != -1]
    if not starts:
        return cleaned

    start = min(starts)
    end_obj = cleaned.rfind("}")
    end_arr = cleaned.rfind("]")
    end = max(end_obj, end_arr)
    if end == -1 or end <= start:
        return cleaned

    return cleaned[start : end + 1]


def parse_food_with_gemini(text: str) -> Any:
    """
    Parse Spanish food input into strict JSON using Gemini REST API.

    Returns a JSON object dictionary with either:
    - {"name": ..., "quantity": ..., "unit": ...}
    - {"error": "invalid_domain" | "insufficient_data"}
    """
    if not settings.GEMINI_API_KEY:
        raise AIParserError("missing_gemini_api_key")

    model_name = settings.GEMINI_MODEL
    endpoint = f"{GEMINI_API_BASE_URL}/{model_name}:generateContent"

    payload: dict[str, Any] = {
        "system_instruction": {
            "parts": [{"text": SYSTEM_PROMPT}],
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": text.strip()}],
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "topK": 1,
            "topP": 0.1,
            "maxOutputTokens": 2048,
            "responseMimeType": "application/json",
        },
    }

    try:
        # Use synchronous httpx for blocking I/O
        client = httpx.Client(timeout=20.0)
        response = client.post(
            endpoint,
            params={"key": settings.GEMINI_API_KEY},
            json=payload,
        )
        response.raise_for_status()
        client.close()
    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code if exc.response is not None else None
        sanitized_url = _sanitize_url_for_logging(str(exc.request.url) if hasattr(exc, 'request') and exc.request else endpoint)
        logger.error("Gemini HTTP status error: %s (URL: %s)", exc, sanitized_url)
        if status_code == 429:
            raise AIParserError("gemini_quota_exceeded") from exc
        raise AIParserError("gemini_request_failed") from exc
    except httpx.HTTPError as exc:
        sanitized_url = _sanitize_url_for_logging(str(exc.request.url) if hasattr(exc, 'request') and exc.request else endpoint)
        logger.error("Gemini request failed: %s (URL: %s)", exc, sanitized_url)
        logger.error("Full exception details: %s", repr(exc))
        raise AIParserError("gemini_request_failed") from exc
    except Exception as exc:
        logger.error("Unexpected error calling Gemini: %s", type(exc).__name__, exc_info=True)
        raise AIParserError("gemini_request_failed") from exc

    try:
        data: dict[str, Any] = response.json()
    except json.JSONDecodeError as exc:
        raise AIParserError("malformed_ai_response") from exc

    raw_text = _extract_text_from_gemini_response(data)

    json_candidate = _extract_json_candidate(raw_text)

    try:
        parsed_json: Any = json.loads(json_candidate)
    except json.JSONDecodeError as exc:
        logger.warning("Gemini returned invalid JSON: %s", raw_text)
        raise AIParserError("invalid_json_response") from exc

    if not isinstance(parsed_json, (dict, list)):
        raise AIParserError("invalid_json_response")

    return parsed_json
