"""Mock AuraNotify page."""

from __future__ import annotations

import os

import dash_mantine_components as dmc
from dash import html

from src.services.mock_data import settings_data as sd
from src.utils.ui_tokens import section_header, settings_page_shell


def build_layout(search: str | None = None) -> html.Div:
    rows = [html.Tr([html.Td(r["group_name"]), html.Td(str(r["sla_percentage"])), html.Td(r["status"])]) for r in sd.MOCK_SLA_ROWS]
    build = os.environ.get("APP_BUILD_ID", "mock")
    return html.Div(
        settings_page_shell(
            [
                section_header("AuraNotify", "Sample SLA rows (static).", icon="solar:graph-new-up-bold-duotone"),
                dmc.Text(f"APP_BUILD_ID={build}", size="xs", c="dimmed", mb="sm"),
                dmc.Paper(
                    p="md",
                    withBorder=True,
                    children=[
                        html.Table(
                            [html.Tr([html.Th("Group"), html.Th("SLA %"), html.Th("Status")]), *rows],
                            style={"width": "100%", "fontSize": "13px"},
                        )
                    ],
                ),
            ]
        )
    )
