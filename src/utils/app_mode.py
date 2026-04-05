"""Application mode helpers (mock demo vs live microservices)."""

from __future__ import annotations

import os


def is_mock_mode() -> bool:
    """True when Dash should use static mock data instead of HTTP APIs."""
    return (os.getenv("APP_MODE") or "").strip().lower() == "mock"
