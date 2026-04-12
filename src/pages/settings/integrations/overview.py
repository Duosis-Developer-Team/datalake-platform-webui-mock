"""Mock integrations overview."""

from __future__ import annotations

import dash_mantine_components as dmc
from dash import html

from src.utils.ui_tokens import section_header, settings_page_shell


def build_layout(search: str | None = None) -> html.Div:
    return html.Div(
        settings_page_shell(
            [
                section_header(
                    "Integrations",
                    "Connector overview (mock).",
                    icon="solar:link-round-angle-bold-duotone",
                ),
                dmc.SimpleGrid(
                    cols=2,
                    children=[
                        dmc.Paper(
                            p="lg",
                            withBorder=True,
                            children=[
                                dmc.Text("LDAP", fw=700),
                                dmc.Text("Status: demo / not connected", size="sm", c="dimmed"),
                                html.A(
                                    dmc.Button("Open LDAP", size="xs", variant="light", color="indigo"),
                                    href="/settings/integrations/ldap",
                                    style={"textDecoration": "none"},
                                ),
                            ],
                        ),
                        dmc.Paper(
                            p="lg",
                            withBorder=True,
                            children=[
                                dmc.Text("AuraNotify", fw=700),
                                dmc.Text("Configure via env in real deployment.", size="sm", c="dimmed"),
                                html.A(
                                    dmc.Button("Open AuraNotify", size="xs", variant="light", color="indigo"),
                                    href="/settings/integrations/auranotify",
                                    style={"textDecoration": "none"},
                                ),
                            ],
                        ),
                    ],
                ),
            ]
        )
    )
