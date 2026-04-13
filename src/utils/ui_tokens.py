"""Shared UI helpers (mirrors Datalake-Platform-GUI src/utils/ui_tokens)."""

from __future__ import annotations

from typing import Any

import dash_mantine_components as dmc
from dash import html
from dash_iconify import DashIconify

PRIMARY = "#552cf8"
PRIMARY_END = "#a092ff"
ON_SURFACE = "#2c2f31"
ON_DIM = "#595c5e"


def card_style(
    *,
    border_left: str | None = None,
    padding: str = "md",
) -> dict[str, Any]:
    style: dict[str, Any] = {
        "borderRadius": "12px",
        "boxShadow": "0 4px 24px rgba(44, 47, 49, 0.06)",
        "background": "#ffffff",
        "border": "1px solid rgba(171, 173, 176, 0.15)",
    }
    if border_left:
        style["borderLeft"] = f"4px solid {border_left}"
    return {"p": padding, "radius": "md", "withBorder": True, "style": style}


def gradient_button_style() -> dict[str, Any]:
    return {
        "background": f"linear-gradient(135deg, {PRIMARY} 0%, {PRIMARY_END} 100%)",
        "border": "none",
        "color": "#fff",
        "fontWeight": 600,
    }


def html_submit_button_gradient(
    label: str,
    *,
    icon: str | None = None,
    style_extra: dict[str, Any] | None = None,
) -> html.Button:
    """Native HTML submit button with gradient styling (parity with GUI)."""
    base: dict[str, Any] = {
        **gradient_button_style(),
        "cursor": "pointer",
        "padding": "10px 20px",
        "borderRadius": "10px",
        "display": "inline-flex",
        "alignItems": "center",
        "gap": "8px",
        "fontSize": "14px",
        "fontFamily": "inherit",
        "boxShadow": "0 2px 8px rgba(85, 44, 248, 0.25)",
    }
    if style_extra:
        base.update(style_extra)
    if icon:
        return html.Button(
            [DashIconify(icon=icon, width=18), label],
            type="submit",
            style=base,
        )
    return html.Button(label, type="submit", style=base)


def html_submit_button_light(
    label: str,
    *,
    scheme: str = "gray",
    small: bool = False,
    style_extra: dict[str, Any] | None = None,
) -> html.Button:
    schemes: dict[str, dict[str, str]] = {
        "gray": {"background": "#f8f9fa", "color": "#495057", "border": "1px solid #dee2e6"},
        "red": {"background": "#fff5f5", "color": "#fa5252", "border": "1px solid #ffc9c9"},
        "indigo": {"background": "#f3f0ff", "color": "#552cf8", "border": "1px solid #d0bfff"},
    }
    s = schemes.get(scheme, schemes["gray"])
    base: dict[str, Any] = {
        **s,
        "cursor": "pointer",
        "borderRadius": "10px",
        "fontFamily": "inherit",
        "fontWeight": 500,
        "padding": "6px 12px" if small else "8px 16px",
        "fontSize": "12px" if small else "13px",
        "transition": "opacity 0.18s ease",
    }
    if style_extra:
        base.update(style_extra)
    return html.Button(label, type="submit", style=base)


def section_header(title: str, subtitle: str | None = None, icon: str | None = None) -> html.Div:
    left = []
    if icon:
        left.append(
            dmc.ThemeIcon(
                DashIconify(icon=icon, width=20),
                size="lg",
                radius="md",
                variant="light",
                color="indigo",
            )
        )
    left.append(
        dmc.Stack(
            gap=2,
            children=[
                dmc.Text(title, fw=800, size="lg", c=ON_SURFACE),
                dmc.Text(subtitle, size="sm", c=ON_DIM) if subtitle else None,
            ],
        )
    )
    return html.Div(dmc.Group(gap="md", align="flex-start", children=left))


def kpi_card(
    label: str,
    value: str | int,
    *,
    icon: str | None = None,
    trend: str | None = None,
    color: str = "indigo",
) -> dmc.Paper:
    top = dmc.Group(
        justify="space-between",
        align="flex-start",
        children=[
            dmc.Stack(
                gap=4,
                children=[
                    dmc.Text(label.upper(), size="xs", fw=700, c="dimmed", style={"letterSpacing": "0.06em"}),
                    dmc.Text(str(value), fw=900, size="xl", c=PRIMARY),
                ],
            ),
            dmc.ThemeIcon(
                DashIconify(icon=icon or "solar:chart-bold-duotone", width=22),
                size="xl",
                radius="md",
                variant="light",
                color=color,
            )
            if icon
            else html.Div(),
        ],
    )
    children = [top]
    if trend:
        children.append(dmc.Text(trend, size="xs", c="dimmed", mt=4))
    return dmc.Paper(children=children, **card_style())


def section_nav_card(
    title: str,
    description: str,
    href: str,
    *,
    icon: str = "solar:widget-bold-duotone",
    badges: list[str] | None = None,
) -> dmc.Card:
    badge_row = (
        dmc.Group(
            gap="xs",
            children=[dmc.Badge(b, size="xs", variant="light", color="indigo") for b in badges],
        )
        if badges
        else None
    )
    inner = dmc.Stack(
        gap="sm",
        children=[
            dmc.Group(
                children=[
                    dmc.ThemeIcon(
                        DashIconify(icon=icon, width=26, color="#fff"),
                        size="xl",
                        radius="md",
                        variant="filled",
                        color="indigo",
                        style={
                            "background": f"linear-gradient(135deg, {PRIMARY} 0%, {PRIMARY_END} 100%)",
                            "border": "none",
                        },
                    ),
                    dmc.Stack(
                        gap=4,
                        children=[
                            dmc.Text(title, fw=800, size="lg", c=ON_SURFACE),
                            dmc.Text(description, size="sm", c=ON_DIM),
                        ],
                    ),
                ],
                align="flex-start",
            ),
            badge_row,
            dmc.Anchor(
                dmc.Button("Open", variant="light", color="indigo", size="xs", radius="md"),
                href=href,
                underline=False,
            ),
        ],
    )
    return dmc.Card(
        withBorder=True,
        radius="md",
        p="lg",
        style={
            "border": "1px solid rgba(171, 173, 176, 0.2)",
            "boxShadow": "0 8px 28px rgba(85, 44, 248, 0.08)",
            "background": "#fff",
        },
        children=[inner],
    )


def settings_page_shell(children: list, *, max_width: str = "1280px") -> html.Div:
    return html.Div(
        style={"maxWidth": max_width, "margin": "0 auto", "paddingBottom": "48px"},
        children=children,
    )
