"""Domain-specific exceptions for Property Underwriter."""

from __future__ import annotations

from typing import Any


class PropertyUnderwriterError(Exception):
    """Base class for predictable, typed errors."""

    def __init__(self, message: str, *, details: Any | None = None) -> None:
        super().__init__(message)
        self.details = details


class ConfigError(PropertyUnderwriterError):
    """Raised when configuration is missing or invalid."""

    def __init__(
        self,
        message: str,
        *,
        details: Any | None = None,
        is_user_error: bool = False,
    ) -> None:
        super().__init__(message, details=details)
        self.is_user_error = is_user_error


class ProviderError(PropertyUnderwriterError):
    """Raised when upstream providers fail."""


class AggregationError(PropertyUnderwriterError):
    """Raised when provider aggregation fails."""


class PersistenceError(PropertyUnderwriterError):
    """Raised when persistence operations fail."""


class ValidationError(PropertyUnderwriterError):
    """Raised when user input fails validation."""
