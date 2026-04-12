"""Mock users page."""

from __future__ import annotations

import dash_mantine_components as dmc
from dash import html

from src.services.mock_data import settings_data as sd
from src.utils.ui_tokens import section_header, settings_page_shell


def build_layout(search: str | None = None) -> html.Div:
    rows = []
    for u in sd.MOCK_USERS:
        rows.append(
            html.Tr(
                [
                    html.Td(u["username"]),
                    html.Td(u.get("display_name", "")),
                    html.Td(u.get("source", "")),
                    html.Td("Yes" if u.get("is_active") else "No"),
                    html.Td(u.get("roles", "")),
                ]
            )
        )
    return html.Div(
        settings_page_shell(
            [
                section_header("Users", "Directory preview (mock).", icon="solar:users-group-rounded-bold-duotone"),
                dmc.Paper(
                    p="md",
                    withBorder=True,
                    children=[
                        html.Table(
                            [
                                html.Tr(
                                    [
                                        html.Th("Username"),
                                        html.Th("Display"),
                                        html.Th("Source"),
                                        html.Th("Active"),
                                        html.Th("Roles"),
                                    ]
                                ),
                                *rows,
                            ],
                            style={"width": "100%", "fontSize": "13px"},
                        )
                    ],
                ),
            ]
        )
    )
