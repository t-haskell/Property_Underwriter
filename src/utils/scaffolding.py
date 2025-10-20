"""Utilities for marking in-progress features and scaffolding work."""
from __future__ import annotations

from functools import wraps
from typing import Any, Callable, Optional, TypeVar, Union, overload

from .logging import logger


class ScaffoldingIncomplete(RuntimeError):
    """Raised when an unfinished feature path is executed during tests."""

    def __init__(self, feature_name: str, message: Optional[str] = None) -> None:
        self.feature_name = feature_name
        default_message = f"Feature '{feature_name}' is not fully implemented yet."
        super().__init__(message or default_message)


def scaffold(feature_name: str, message: Optional[str] = None) -> None:
    """Log intent and raise :class:`ScaffoldingIncomplete` for a feature."""

    logger.info("Scaffolding invoked for feature '%s'", feature_name)
    raise ScaffoldingIncomplete(feature_name, message=message)


F = TypeVar("F", bound=Callable[..., Any])


def _wrap_scaffoldable(func: F, feature_name: Optional[str]) -> F:
    name = feature_name or func.__qualname__

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        scaffold(name)

    return wrapper  # type: ignore[return-value]


@overload
def scaffoldable(func: F) -> F:
    ...


@overload
def scaffoldable(*, feature_name: str) -> Callable[[F], F]:
    ...


def scaffoldable(
    func: Optional[F] = None,
    *,
    feature_name: Optional[str] = None,
) -> Union[F, Callable[[F], F]]:
    """Decorator that raises :class:`ScaffoldingIncomplete` when executed."""

    if func is not None:
        return _wrap_scaffoldable(func, feature_name)

    def decorator(inner: F) -> F:
        return _wrap_scaffoldable(inner, feature_name)

    return decorator
