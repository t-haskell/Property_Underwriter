"""Lightweight fallback stub for the ``httpx`` module used in tests.

The real application depends on the third-party ``httpx`` package. The test
suite monkeypatches the ``httpx.get`` function heavily, so the stub only needs a
minimal surface area to satisfy attribute lookups when the dependency is not
installed in the execution environment.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any


class HTTPError(Exception):
    """Replacement for ``httpx.HTTPError`` when the package is unavailable."""


class Response:
    """Simple response object compatible with the provider tests."""

    def __init__(self, status_code: int = 200, text: str = "", json_data: Any | None = None):
        self.status_code = status_code
        self.text = text
        self._json_data = json_data

    @property
    def is_error(self) -> bool:
        return self.status_code >= 400

    def json(self) -> Any:
        if self._json_data is None:
            raise ValueError("No JSON data configured for stub response")
        return self._json_data


def _not_implemented(*args: Any, **kwargs: Any):  # pragma: no cover - should be monkeypatched in tests
    raise RuntimeError(
        "httpx is not installed. Tests should monkeypatch 'httpx.get' before calling the providers."
    )


httpx = SimpleNamespace(HTTPError=HTTPError, Response=Response, get=_not_implemented)

__all__ = ["HTTPError", "Response", "httpx"]
