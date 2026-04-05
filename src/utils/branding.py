"""UI brand title from environment (demo / white-label)."""

import os

_DEFAULT_BRAND_TITLE = "Datalake WebUI"


def get_brand_title() -> str:
    """Sidebar and browser tab title. Override with APP_BRAND_TITLE for per-customer demos."""
    raw = (os.getenv("APP_BRAND_TITLE") or "").strip()
    return raw if raw else _DEFAULT_BRAND_TITLE
