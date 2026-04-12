"""Mock audit log page."""

from __future__ import annotations

import dash_mantine_components as dmc
from dash import html

from src.services.mock_data import settings_data as sd
from src.utils.ui_tokens import section_header, settings_page_shell


def build_layout(search: str | None = None) -> html.Div:
    rows = []
    for x in sd.MOCK_AUDIT:
        rows.append(
            html.Tr(
                [
                    html.Td(x["created_at"][:19]),
                    html.Td(x["username"]),
                    html.Td(x["action"]),
                    html.Td(x.get("detail", "")),
                ]
            )
        )
    return html.Div(
        settings_page_shell(
            [
                section_header("Audit log", "Mock audit entries.", icon="solar:clipboard-list-bold-duotone"),
                dmc.Paper(
                    p="md",
                    withBorder=True,
                    children=[
                        html.Table(
                            [html.Tr([html.Th("Time"), html.Th("User"), html.Th("Action"), html.Th("Detail")]), *rows],
                            style={"width": "100%", "fontSize": "13px"},
                        )
                    ],
                ),
            ]
        )
    )
