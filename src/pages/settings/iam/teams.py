"""Mock teams page."""

from __future__ import annotations

import dash_mantine_components as dmc
from dash import html

from src.services.mock_data import settings_data as sd
from src.utils.ui_tokens import section_header, settings_page_shell


def build_layout(search: str | None = None) -> html.Div:
    rows = [
        html.Tr(
            [
                html.Td(str(t["id"])),
                html.Td(t["name"]),
                html.Td(t["created_by"]),
                html.Td(str(t["member_count"])),
            ]
        )
        for t in sd.MOCK_TEAMS
    ]
    return html.Div(
        settings_page_shell(
            [
                section_header("Teams", "Team list (mock).", icon="solar:users-group-two-rounded-bold-duotone"),
                dmc.Paper(
                    p="md",
                    withBorder=True,
                    children=[
                        html.Table(
                            [html.Tr([html.Th("ID"), html.Th("Name"), html.Th("Lead"), html.Th("Members")]), *rows],
                            style={"width": "100%", "fontSize": "13px"},
                        )
                    ],
                ),
            ]
        )
    )
