"""Mock Settings landing — KPIs, section cards, audit snippet."""

from __future__ import annotations

import dash_mantine_components as dmc
from dash import html

from src.services.mock_data import settings_data as sd
from src.utils.ui_tokens import ON_SURFACE, kpi_card, section_header, section_nav_card, settings_page_shell


def build_layout(search: str | None = None) -> html.Div:
    active = sum(1 for u in sd.MOCK_USERS if u.get("is_active"))
    inactive = len(sd.MOCK_USERS) - active
    kpi = dmc.SimpleGrid(
        cols=4,
        spacing="md",
        children=[
            kpi_card("Active users", active, icon="solar:users-group-rounded-bold-duotone", color="green"),
            kpi_card("Inactive users", inactive, icon="solar:user-block-bold-duotone", color="gray"),
            kpi_card("Teams", len(sd.MOCK_TEAMS), icon="solar:users-group-two-rounded-bold-duotone", color="indigo"),
            kpi_card("Roles", 3, icon="solar:shield-user-bold-duotone", color="violet"),
        ],
    )
    cards = dmc.SimpleGrid(
        cols=2,
        spacing="lg",
        children=[
            section_nav_card(
                "Identity & Access Management",
                "Users, teams, roles, and audit (mock data).",
                "/settings/iam/users",
                icon="solar:shield-user-bold-duotone",
                badges=["Mock mode"],
            ),
            section_nav_card(
                "Integrations",
                "LDAP & AuraNotify placeholders.",
                "/settings/integrations",
                icon="solar:link-round-angle-bold-duotone",
                badges=["Demo"],
            ),
        ],
    )
    rows = []
    for x in sd.MOCK_AUDIT:
        rows.append(
            html.Tr(
                [
                    html.Td(str(x.get("created_at", ""))[:19]),
                    html.Td(x.get("username")),
                    html.Td(x.get("action")),
                    html.Td(x.get("detail", "")[:60]),
                ]
            )
        )
    audit = dmc.Paper(
        p="md",
        withBorder=True,
        children=[
            dmc.Text("Recent activity (mock)", fw=700, mb="sm", c=ON_SURFACE),
            html.Table(
                [html.Tr([html.Th("Time"), html.Th("User"), html.Th("Action"), html.Th("Detail")]), *rows],
                style={"width": "100%", "fontSize": "13px"},
            ),
        ],
    )
    hero = dmc.Paper(
        p="xl",
        radius="md",
        mb="lg",
        style={
            "background": "linear-gradient(135deg, #f6f2ff 0%, #ede8ff 55%, #ffffff 100%)",
            "border": "1px solid rgba(85, 44, 248, 0.12)",
        },
        children=[
            dmc.Title("Settings overview", order=3, c=ON_SURFACE),
            dmc.Text("Mock WebUI — data is illustrative only.", size="sm", c="dimmed"),
        ],
    )
    return html.Div(settings_page_shell([hero, kpi, dmc.Space(h="lg"), cards, dmc.Space(h="lg"), audit]))
