"""Mock auth settings page (stub)."""

from __future__ import annotations

import dash_mantine_components as dmc
from dash import html

from src.utils.ui_tokens import section_header, settings_page_shell


def build_layout(search: str | None = None) -> html.Div:
    return html.Div(
        settings_page_shell(
            [
                section_header(
                    "Auth settings",
                    "Environment-driven flags are shown in the full GUI.",
                    icon="solar:lock-keyhole-bold-duotone",
                ),
                dmc.Alert(
                    "This section uses live data in the full platform. Mock UI shows layout only.",
                    color="blue",
                    variant="light",
                ),
            ]
        )
    )
