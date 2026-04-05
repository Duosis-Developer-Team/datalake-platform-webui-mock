"""Analytics dashboard (mock data only — enabled when APP_MODE=mock)."""

from __future__ import annotations

import plotly.graph_objects as go
from dash import dcc, html
import dash_mantine_components as dmc
from dash_iconify import DashIconify

from src.services.mock_data.analytics import (
    get_capacity_forecast_series,
    get_cost_optimization,
    get_efficiency_scores,
    get_risk_radar,
)
from src.utils.time_range import default_time_range


def _card(title: str, subtitle: str | None, children, icon: str = "solar:chart-square-bold-duotone"):
    return html.Div(
        className="nexus-card",
        style={"padding": "20px", "marginBottom": "20px"},
        children=[
            dmc.Group(
                gap="sm",
                align="center",
                mb="md",
                children=[
                    DashIconify(icon=icon, width=26, color="#4318FF"),
                    html.Div(
                        children=[
                            html.H3(title, style={"margin": 0, "color": "#2B3674", "fontSize": "1.05rem"}),
                            html.P(subtitle, style={"margin": "4px 0 0 0", "color": "#A3AED0", "fontSize": "0.8rem"})
                            if subtitle
                            else None,
                        ]
                    ),
                ],
            ),
            children,
        ],
    )


def build_analytics(time_range=None):
    tr = time_range or default_time_range()
    forecast = get_capacity_forecast_series()
    eff = get_efficiency_scores()
    risks = get_risk_radar()
    cost = get_cost_optimization()

    fig_forecast = go.Figure()
    for dc, series in (forecast.get("by_dc") or {}).items():
        hist_x = [p["day"] for p in series if p.get("phase") == "hist"]
        hist_y = [p["cpu_pct"] for p in series if p.get("phase") == "hist"]
        fc_x = [p["day"] for p in series if p.get("phase") == "forecast"]
        fc_y = [p["cpu_pct"] for p in series if p.get("phase") == "forecast"]
        fig_forecast.add_trace(go.Scatter(x=hist_x, y=hist_y, mode="lines", name=f"{dc} (hist)", legendgroup=dc))
        fig_forecast.add_trace(
            go.Scatter(
                x=fc_x,
                y=fc_y,
                mode="lines",
                line=dict(dash="dash"),
                name=f"{dc} (forecast)",
                legendgroup=dc,
                showlegend=True,
            )
        )
    fig_forecast.update_layout(
        margin=dict(l=40, r=20, t=30, b=40),
        height=320,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans", color="#2B3674"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    )
    fig_forecast.update_xaxes(title="Day index")
    fig_forecast.update_yaxes(title="CPU %")

    eff_labels = [e["dc"] for e in eff]
    eff_vals = [e["efficiency_score"] for e in eff]
    fig_eff = go.Figure(
        data=[go.Bar(x=eff_labels, y=eff_vals, marker_color="#4318FF", text=[f"{v:.0f}" for v in eff_vals], textposition="outside")]
    )
    fig_eff.update_layout(
        margin=dict(l=40, r=20, t=20, b=40),
        height=280,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans"),
        yaxis=dict(range=[0, 100], title="Score"),
    )

    risk_colors = {"high": "#FA896B", "medium": "#FFB547", "low": "#05CD99", "info": "#A3AED0"}
    risk_badges = [
        dmc.Paper(
            p="sm",
            withBorder=True,
            children=[
                dmc.Group(
                    justify="space-between",
                    children=[
                        dmc.Text(r["dc"], fw=700, size="sm"),
                        dmc.Badge(r["severity"].upper(), color=risk_colors.get(r["severity"], "gray"), variant="light"),
                    ],
                ),
                dmc.Text(r["risk"], size="xs", c="dimmed", mt=4),
                dmc.Text(f"ETA: {r['eta_days']} days" if r.get("eta_days") else "ETA: n/a", size="xs", mt=4),
            ],
        )
        for r in risks
    ]

    zombies = cost.get("zombie_vms") or []
    zombie_rows = [
        dmc.Group(
            justify="space-between",
            children=[
                dmc.Text(z["name"], size="sm", fw=600),
                dmc.Text(f"{z['dc']} · {z['cpu']} vCPU · ~{z['monthly_cost_eur']} EUR/mo", size="xs", c="dimmed"),
            ],
        )
        for z in zombies
    ]

    return html.Div(
        [
            html.Div(
                className="nexus-glass",
                style={"padding": "24px 32px", "marginBottom": "24px"},
                children=[
                    dmc.Group(
                        gap="sm",
                        align="center",
                        children=[
                            DashIconify(icon="solar:chart-square-bold-duotone", width=32, color="#4318FF"),
                            html.H1(
                                "Analytics",
                                style={"margin": 0, "color": "#2B3674", "fontSize": "1.8rem"},
                            ),
                        ],
                    ),
                    html.P(
                        "Mock capacity forecast, efficiency, risk, and cost views (APP_MODE=mock).",
                        style={"margin": "8px 0 0 44px", "color": "#A3AED0"},
                    ),
                ],
            ),
            _card(
                "Capacity forecast",
                "Historical + projected CPU utilisation by datacenter",
                dcc.Graph(figure=fig_forecast, config={"displayModeBar": False}, style={"height": "340px"}),
            ),
            dmc.SimpleGrid(
                cols={"base": 1, "md": 2},
                spacing="lg",
                children=[
                    _card(
                        "Environment efficiency",
                        "Composite efficiency score per site",
                        dcc.Graph(figure=fig_eff, config={"displayModeBar": False}, style={"height": "300px"}),
                        icon="solar:graph-new-up-bold-duotone",
                    ),
                    _card(
                        "Anomaly & risk radar",
                        "Executive risk cards (mock scenarios)",
                        dmc.Stack(gap="sm", children=risk_badges),
                        icon="solar:danger-triangle-bold-duotone",
                    ),
                ],
            ),
            _card(
                "Cost optimization",
                "Zombie VMs and idle storage (illustrative savings)",
                dmc.Stack(
                    gap="md",
                    children=[
                        dmc.Group(
                            gap="xl",
                            children=[
                                dmc.Text(f"Idle storage: {cost.get('idle_storage_tb', 0)} TB", fw=600),
                                dmc.Text(
                                    f"Potential savings: ~{cost.get('potential_monthly_savings_eur', 0):,.0f} EUR/mo",
                                    fw=700,
                                    c="teal",
                                ),
                            ],
                        ),
                        dmc.Divider(),
                        *zombie_rows,
                    ],
                ),
                icon="solar:wallet-money-bold-duotone",
            ),
        ]
    )
