"""Shared error-handling utilities for API endpoints."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from fastapi import HTTPException, status

from .custom_exceptions import NovaFitnessException


@contextmanager
def service_error_handler(default_detail: str = "An unexpected error occurred") -> Iterator[None]:
    """Context manager that eliminates the two boilerplate except clauses in every endpoint.

    - Re-raises ``HTTPException`` as-is (so FastAPI processes it normally).
    - Re-raises ``NovaFitnessException`` subclasses as-is so the caller's
      domain-specific ``except`` blocks (404, 422, etc.) can handle them.
    - Converts any other unexpected exception to HTTP 500 with *default_detail*.
    """
    try:
        yield
    except (HTTPException, NovaFitnessException):
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=default_detail,
        )
