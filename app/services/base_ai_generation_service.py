"""Base class for AI-powered generation services (diet, routine).

Owns the shared generate/edit control flow: upsert → Gemini → HTML → status update.
Subclasses implement domain-specific logic via abstract methods.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class BaseAIGenerationService(ABC):
    """Abstract base for services that generate/edit content via Gemini AI.

    Subclasses implement domain-specific logic; this class owns the shared
    generate/edit control flow: upsert → Gemini → HTML → status update.
    """

    # ── Abstract interface ──────────────────────────────────────────────────

    @classmethod
    @abstractmethod
    def _upsert_record(
        cls, db: Session, *, user_id: int, intake: dict[str, Any]
    ) -> Any:
        """Create or update the domain record with PROCESSING status. Return it."""

    @classmethod
    @abstractmethod
    def _get_active_record(cls, db: Session, *, user_id: int) -> Any:
        """Return the active record or raise a domain NotFoundError."""

    @classmethod
    @abstractmethod
    def _get_record_data(cls, record: Any) -> dict[str, Any] | None:
        """Return the stored data dict from the record (e.g. record.diet_data)."""

    @classmethod
    @abstractmethod
    def _set_record_ready(
        cls, record: Any, *, raw_data: dict[str, Any], html: str
    ) -> None:
        """Set all fields needed when generation succeeds (status, data, html, etc.)."""

    @classmethod
    @abstractmethod
    def _set_record_error(cls, record: Any, *, error_message: str) -> None:
        """Set status=ERROR and store error_message on the record."""

    @classmethod
    @abstractmethod
    def _build_generation_prompt(
        cls,
        intake: dict[str, Any],
        free_text: str,
        user_bio: dict[str, Any],
        **kwargs: Any,
    ) -> str:
        """Build the full prompt for initial generation."""

    @classmethod
    @abstractmethod
    def _build_edit_prompt(
        cls, current_data: dict[str, Any], edit_instruction: str
    ) -> str:
        """Build the full prompt for editing an existing record."""

    @classmethod
    @abstractmethod
    def _call_gemini_and_parse(cls, prompt: str) -> dict[str, Any]:
        """Call Gemini API and return parsed JSON dict. Raise domain error on failure."""

    @classmethod
    @abstractmethod
    def _generate_html(cls, raw_data: dict[str, Any]) -> str:
        """Convert parsed Gemini output into self-contained HTML."""

    # ── Optional hook ───────────────────────────────────────────────────────

    @classmethod
    def _post_process(cls, raw_data: dict[str, Any], **kwargs: Any) -> None:
        """Optional: enrich raw_data in-place after Gemini call.
        Default is no-op. Override in DietService for FatSecret enrichment."""

    # ── Shared concrete workflow ────────────────────────────────────────────

    @classmethod
    def generate_from_text(
        cls,
        db: Session,
        *,
        user_id: int,
        intake: dict[str, Any],
        free_text: str,
        user_bio: dict[str, Any],
        **kwargs: Any,
    ) -> Any:
        """Generate a new record from intake + bio via Gemini."""
        record = cls._upsert_record(db, user_id=user_id, intake=intake)
        db.commit()

        try:
            prompt = cls._build_generation_prompt(intake, free_text, user_bio, **kwargs)
            raw_data = cls._call_gemini_and_parse(prompt)
            cls._post_process(raw_data, **kwargs)
            html = cls._generate_html(raw_data)
            cls._set_record_ready(record, raw_data=raw_data, html=html)
        except Exception as exc:
            logger.exception("AI generation failed for user_id=%s", user_id)
            cls._set_record_error(record, error_message=str(exc))

        db.commit()
        db.refresh(record)
        return record

    @classmethod
    def edit_record(
        cls,
        db: Session,
        *,
        user_id: int,
        edit_instruction: str,
    ) -> Any:
        """Edit an existing record using Gemini."""
        record = cls._get_active_record(db, user_id=user_id)

        current_data = cls._get_record_data(record)
        if not current_data:
            raise cls._get_no_data_exception()

        cls._set_record_processing(record)
        db.commit()

        try:
            prompt = cls._build_edit_prompt(current_data, edit_instruction)
            raw_data = cls._call_gemini_and_parse(prompt)
            cls._post_process(raw_data)
            html = cls._generate_html(raw_data)
            cls._set_record_ready(record, raw_data=raw_data, html=html)
        except Exception as exc:
            logger.exception("AI edit failed for user_id=%s", user_id)
            cls._set_record_error(record, error_message=str(exc))

        db.commit()
        db.refresh(record)
        return record

    @classmethod
    def _set_record_processing(cls, record: Any) -> None:
        """Set record status to PROCESSING. Override if status constant differs."""
        record.status = "processing"

    @classmethod
    def _get_no_data_exception(cls) -> Exception:
        """Return the exception to raise when record has no data to edit."""
        return ValueError("No data available to edit.")
