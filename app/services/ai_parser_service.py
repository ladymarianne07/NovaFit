import json
import logging
from typing import Any
import re

import httpx

from ..config import settings


logger = logging.getLogger(__name__)

_GEMINI_HTTP_CLIENT = httpx.Client(timeout=20.0)

# Configure httpx logging to suppress sensitive information
logging.getLogger("httpx").setLevel(logging.WARNING)


def _sanitize_url_for_logging(url: str) -> str:
    """Remove API keys from URL before logging."""
    return re.sub(r'key=[^&\s]+', 'key=***REDACTED***', url)


def _api_key_fingerprint(api_key: str | None) -> str:
    """Return non-sensitive API key fingerprint for diagnostics."""
    if not api_key:
        return "<missing>"
    if len(api_key) <= 8:
        return "***"
    return f"{api_key[:4]}...{api_key[-4:]}"


GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
FALLBACK_GEMINI_MODELS: tuple[str, ...] = (
    "gemini-2.5-flash",
    "gemini-2.0-flash",
)

SYSTEM_PROMPT = (
    "You are a precise nutrition parser for a fitness tracking application.\n"
    "Input is in Spanish (or occasionally English). Always translate food names to English in the output.\n"
    "Output ONLY valid JSON. No explanations, no markdown, no code fences.\n"
    "\n"
    "=== INPUT VALIDATION ===\n"
    "If the input has nothing to do with food or eating (e.g. emotions, exercise descriptions without food, random text, greetings): return {\"error\": \"invalid_domain\"}\n"
    "If the input mentions food but no quantity can be determined or reasonably inferred: return {\"error\": \"insufficient_data\"}\n"
    "If the user explicitly states they ate nothing ('no comí nada', 'no comí', 'ayuné', 'estuve en ayunas', 'nada hoy', 'fasted'): return {\"zero_intake\": true}\n"
    "\n"
    "=== SIZE & VESSEL RESOLUTION ===\n"
    "Convert ambiguous vessels and qualitative sizes to concrete quantities before outputting.\n"
    "Vessels:\n"
    "  - 'vaso' / 'glass' → {\"quantity\": 250, \"unit\": \"ml\"}\n"
    "  - 'bowl' / 'tazón' → solids: {\"quantity\": 1, \"unit\": \"serving\"} | liquids: {\"quantity\": 350, \"unit\": \"ml\"}\n"
    "Eggs — always convert to grams (do NOT use 'piece' for eggs):\n"
    "  - 1 huevo / 1 egg → 60g | 2 huevos / 2 eggs → 120g | 3 huevos → 180g\n"
    "Fruits with qualitative size:\n"
    "  - banana pequeña → 80g, mediana → 120g, grande → 150g\n"
    "  - manzana pequeña → 120g, mediana → 182g, grande → 242g\n"
    "  - naranja mediana → 130g | tomate mediano → 120g\n"
    "  - 'un scoop de proteína en polvo' / '1 scoop protein powder' → 30g\n"
    "  - 'plato de' / 'plate of' → {\"quantity\": 1, \"unit\": \"serving\"}\n"
    "For any other food with 'mediano/a', 'grande', 'pequeño/a' → convert to a reasonable gram estimate.\n"
    "\n"
    "=== SUPPLEMENTS ===\n"
    "Sports supplements are NOT caloric food. Return them as items with \"is_supplement\": true.\n"
    "Recognized supplements: creatine/creatina, beta alanine/beta alanina, BCAA, glutamine/glutamina,\n"
    "pre-workout, collagen/colágeno, magnesium/magnesio, zinc, vitamin supplements/vitaminas.\n"
    "Example: {\"name\": \"creatine monohydrate\", \"quantity\": 5, \"unit\": \"grams\", \"is_supplement\": true}\n"
    "Do NOT return {\"error\": \"invalid_domain\"} for supplement-only inputs.\n"
    "\n"
    "=== RECIPE / PREPARATION HANDLING ===\n"
    "Detect recipe context when the user describes MAKING something with ingredients and eating a portion.\n"
    "Trigger words: 'hice', 'preparé', 'cociné', 'prepare', 'made', 'cooked'.\n"
    "Steps:\n"
    "  1. List all ingredients with their TOTAL quantities as given.\n"
    "  2. Determine eaten_portions and total_portions to calculate factor = eaten / total.\n"
    "     - 'me comí 2 porciones de 10' → factor = 2/10 = 0.2\n"
    "     - 'me comí la mitad' → factor = 0.5\n"
    "     - 'me comí una porción' (no total given) → factor = 0.25\n"
    "     - No portion info at all → factor = 1.0 (ate the full recipe)\n"
    "  3. Multiply each ingredient quantity by factor. Return all in grams.\n"
    "Example: 'Hice pan con 500g harina, 200g manteca, 2 huevos. Me comí 2 porciones de 10'\n"
    "  factor=0.2 → flour=100g, butter=40g, eggs=120g*0.2=24g\n"
    "Output: {\"items\": [{\"name\": \"wheat flour\", \"quantity\": 100, \"unit\": \"grams\"}, {\"name\": \"butter\", \"quantity\": 40, \"unit\": \"grams\"}, {\"name\": \"egg\", \"quantity\": 24, \"unit\": \"grams\"}]}\n"
    "\n"
    "=== STANDARD FOOD HANDLING ===\n"
    "Extract all food items mentioned. Ignore meal labels (desayuno, almuerzo, cena, etc.) — return only food items.\n"
    "Split combined foods into separate items (e.g. 'cafe con leche' → coffee + milk, 'pollo con arroz' → chicken + rice).\n"
    "Include garnishes with near-zero calories (lemon juice/jugo de limón, vinegar, herbs) — they will not inflate the total.\n"
    "If quantity is not specified, infer one standard serving (quantity: 1, unit: 'serving').\n"
    "\n"
    "=== OUTPUT FORMAT ===\n"
    "Single item:   {\"name\": \"english name\", \"quantity\": number, \"unit\": \"grams\"|\"serving\"|\"cup\"|\"tablespoon\"|\"teaspoon\"|\"ml\"}\n"
    "Multiple items: {\"items\": [{\"name\": \"english name\", \"quantity\": number, \"unit\": \"...\"}]}\n"
    "Rules:\n"
    "  - Prefer 'grams' whenever exact weight is known or can be calculated.\n"
    "  - Use 'serving' only when no concrete quantity can be determined.\n"
    "  - quantity must always be a positive number.\n"
)


class AIParserError(Exception):
    """Raised when Gemini parser fails or returns invalid response."""


def _normalize_model_name(model_name: str) -> str:
    """Normalize model names from env/config to Gemini endpoint-safe format."""
    normalized = (model_name or "").strip().strip("/")
    if not normalized:
        return ""

    if normalized.lower().startswith("models/"):
        normalized = normalized[len("models/") :]

    if ":" in normalized:
        normalized = normalized.split(":", 1)[0]

    return normalized.lower()


def _build_model_candidates(primary_model: str) -> list[str]:
    candidates: list[str] = []

    normalized_primary = _normalize_model_name(primary_model)
    if normalized_primary:
        candidates.append(normalized_primary)

    for fallback_model in FALLBACK_GEMINI_MODELS:
        normalized_fallback = _normalize_model_name(fallback_model)
        if normalized_fallback and normalized_fallback not in candidates:
            candidates.append(normalized_fallback)
    return candidates


def _is_model_not_found_response(status_code: int | None, response_text: str) -> bool:
    if status_code != 404:
        return False

    lowered = (response_text or "").lower()
    return (
        "not found" in lowered
        or "not supported for generatecontent" in lowered
        or "call listmodels" in lowered
    )


def _is_invalid_model_format_response(status_code: int | None, response_text: str) -> bool:
    if status_code != 400:
        return False

    lowered = (response_text or "").lower()
    return (
        "unexpected model name format" in lowered
        or "generatecontentrequest.model" in lowered
    )


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

    configured_model = _normalize_model_name(settings.GEMINI_MODEL)
    model_candidates = _build_model_candidates(configured_model)
    response: httpx.Response | None = None
    model_not_found_failures = 0

    for model_name in model_candidates:
        endpoint = f"{GEMINI_API_BASE_URL}/{model_name}:generateContent"
        try:
            response = _GEMINI_HTTP_CLIENT.post(
                endpoint,
                params={"key": settings.GEMINI_API_KEY},
                json=payload,
            )
            response.raise_for_status()
            if model_name != configured_model:
                logger.warning(
                    "Gemini fallback model used: configured=%s selected=%s",
                    configured_model,
                    model_name,
                )
            break
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            response_preview = ""
            if exc.response is not None:
                try:
                    response_preview = exc.response.text[:600]
                except Exception:
                    response_preview = "<unavailable_response_body>"

            sanitized_url = _sanitize_url_for_logging(
                str(exc.request.url) if hasattr(exc, "request") and exc.request else endpoint
            )

            if status_code == 429:
                logger.error(
                    "Gemini quota exceeded (URL: %s, key=%s, body=%s)",
                    sanitized_url,
                    _api_key_fingerprint(settings.GEMINI_API_KEY),
                    response_preview,
                )
                raise AIParserError("gemini_quota_exceeded") from exc

            if _is_model_not_found_response(status_code, response_preview) or _is_invalid_model_format_response(status_code, response_preview):
                model_not_found_failures += 1
                logger.warning(
                    "Gemini model unavailable: %s (URL: %s, key=%s)",
                    model_name,
                    sanitized_url,
                    _api_key_fingerprint(settings.GEMINI_API_KEY),
                )
                continue

            logger.error(
                "Gemini HTTP status error: %s (URL: %s, key=%s, body=%s)",
                exc,
                sanitized_url,
                _api_key_fingerprint(settings.GEMINI_API_KEY),
                response_preview,
            )
            raise AIParserError("gemini_request_failed") from exc
        except httpx.HTTPError as exc:
            sanitized_url = _sanitize_url_for_logging(
                str(exc.request.url) if hasattr(exc, "request") and exc.request else endpoint
            )
            logger.error("Gemini request failed: %s (URL: %s)", exc, sanitized_url)
            logger.error("Full exception details: %s", repr(exc))
            raise AIParserError("gemini_request_failed") from exc
        except Exception as exc:
            logger.error("Unexpected error calling Gemini: %s", type(exc).__name__, exc_info=True)
            raise AIParserError("gemini_request_failed") from exc

    if response is None:
        if model_not_found_failures > 0:
            raise AIParserError("gemini_model_not_found")
        raise AIParserError("gemini_request_failed")

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
