"""
Base application exceptions for Quantum Market Intelligence.
"""

from __future__ import annotations

from typing import Any


class QMIException(Exception):
    """Base exception for controlled QMI application errors."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details

        super().__init__(message)