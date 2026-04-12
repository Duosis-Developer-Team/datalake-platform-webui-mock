"""Mock LDAP page."""

from __future__ import annotations

import dash_mantine_components as dmc
from dash import html

from src.utils.ui_tokens import section_header, settings_page_shell


def build_layout(search: str | None = None) -> html.Div:
    return html.Div(
        settings_page_shell(
            [
                section_header("LDAP", "Mock — no bind performed here.", icon="solar:key-minimalistic-bold-duotone"),
                dmc.Alert("Forms post to /auth in the full GUI only.", color="yellow", variant="light"),
            ]
        )
    )
