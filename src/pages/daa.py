"""Datalake Assistant Agent (DAA) page — mock chat, report builder, exports."""

from __future__ import annotations

import plotly.graph_objects as go
import dash
import pandas as pd
from dash import ALL, Input, Output, State, callback_context, dcc, dash_table, html, no_update
import dash_mantine_components as dmc
from dash_iconify import DashIconify

from src.services.mock_data.daa_scenarios import (
    daa_report_rows,
    get_canned_answer,
    match_scenario,
    quick_actions_for_path,
)
from src.services.mock_data.datacenters import MOCK_DC_CODES
from src.utils.export_helpers import (
    build_report_info_df,
    csv_bytes_with_report_header,
    dash_send_csv_bytes,
    dash_send_excel_workbook,
    dataframes_to_excel_with_meta,
)
from src.utils.time_range import default_time_range


def _report_figure(cols: list[str], rows: list[list]) -> go.Figure:
    if not rows or not cols:
        return go.Figure()
    c0 = cols[0]
    try:
        x = [r[0] for r in rows]
        ycol = cols[1] if len(cols) > 1 else cols[0]
        yi = cols.index(ycol)
        y = [float(r[yi]) if yi < len(r) and isinstance(r[yi], (int, float)) else 0 for r in rows]
        fig = go.Figure(data=[go.Bar(x=x, y=y, marker_color="#4318FF")])
    except Exception:
        fig = go.Figure()
    fig.update_layout(
        margin=dict(l=40, r=20, t=30, b=40),
        height=280,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans", color="#2B3674"),
    )
    return fig


def build_daa_page(time_range=None):
    tr = time_range or default_time_range()
    _ = tr
    qa = quick_actions_for_path("/daa")
    qa_buttons = [
        dmc.Button(
            a["label"],
            id={"type": "daa-qa", "idx": a["id"]},
            size="xs",
            variant="light",
            color="indigo",
            mb=6,
        )
        for a in qa
    ]
    cols, rows = daa_report_rows("summary", None)
    df = pd.DataFrame(rows, columns=cols)
    data = df.to_dict("records")
    columns = [{"name": c, "id": c} for c in cols]
    fig = _report_figure(cols, rows)

    return html.Div(
        [
            dcc.Store(id="daa-report-store", data={"columns": cols, "rows": rows}),
            dcc.Download(id="daa-download-excel"),
            dcc.Download(id="daa-download-csv"),
            html.Div(
                className="nexus-glass",
                style={"padding": "24px 32px", "marginBottom": "24px"},
                children=[
                    dmc.Group(
                        gap="sm",
                        align="center",
                        children=[
                            DashIconify(icon="solar:chat-round-dots-bold-duotone", width=32, color="#4318FF"),
                            html.H1(
                                "Datalake Assistant Agent",
                                style={"margin": 0, "color": "#2B3674", "fontSize": "1.8rem"},
                            ),
                        ],
                    ),
                    html.P(
                        "Mock assistant: quick questions, custom reports, Excel/CSV export (APP_MODE=mock).",
                        style={"margin": "8px 0 0 44px", "color": "#A3AED0"},
                    ),
                ],
            ),
            dmc.SimpleGrid(
                cols={"base": 1, "md": 2},
                spacing="lg",
                children=[
                    html.Div(
                        className="nexus-card",
                        style={"padding": "20px"},
                        children=[
                            html.H3("Conversation", style={"margin": "0 0 12px 0", "color": "#2B3674", "fontSize": "1rem"}),
                            html.Div(
                                id="daa-chat-log",
                                style={"minHeight": "160px", "maxHeight": "240px", "overflowY": "auto", "marginBottom": "12px"},
                                children=[dmc.Text("Try a quick action or type a question (mock).", size="sm", c="dimmed")],
                            ),
                            html.Div(qa_buttons),
                            dmc.Group(
                                mt="md",
                                grow=True,
                                children=[
                                    dmc.TextInput(id="daa-chat-input", placeholder="Ask about capacity, cost, health...", style={"flex": 1}),
                                    dmc.Button("Send", id="daa-chat-send", color="indigo", variant="filled"),
                                ],
                            ),
                        ],
                    ),
                    html.Div(
                        className="nexus-card",
                        style={"padding": "20px"},
                        children=[
                            html.H3("Custom report", style={"margin": "0 0 12px 0", "color": "#2B3674", "fontSize": "1rem"}),
                            dmc.Select(
                                id="daa-report-type",
                                label="Report type",
                                data=[
                                    {"value": "summary", "label": "Executive summary"},
                                    {"value": "capacity", "label": "Capacity outlook"},
                                    {"value": "risk", "label": "Risk register"},
                                ],
                                value="summary",
                                mb="md",
                            ),
                            dmc.Select(
                                id="daa-dc-filter",
                                label="Datacenter filter (optional)",
                                data=[{"value": "", "label": "All datacenters"}]
                                + [{"value": c, "label": c} for c in MOCK_DC_CODES],
                                value="",
                                mb="md",
                            ),
                            dmc.Button("Generate report", id="daa-generate", color="indigo", fullWidth=True),
                            dmc.Group(
                                mt="md",
                                gap="sm",
                                children=[
                                    dmc.Button("Export Excel", id="daa-export-xlsx", variant="light", color="gray"),
                                    dmc.Button("Export CSV", id="daa-export-csv", variant="light", color="gray"),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
            html.Div(
                className="nexus-card",
                style={"padding": "20px", "marginTop": "20px"},
                children=[
                    html.H3("Report preview", style={"margin": "0 0 12px 0", "color": "#2B3674", "fontSize": "1rem"}),
                    dash_table.DataTable(
                        id="daa-report-table",
                        columns=columns,
                        data=data,
                        page_size=12,
                        style_table={"overflowX": "auto"},
                        style_cell={"fontFamily": "DM Sans, sans-serif", "fontSize": "12px"},
                        style_header={"fontWeight": "600", "backgroundColor": "#F4F7FE"},
                    ),
                    dcc.Graph(id="daa-report-chart", figure=fig, config={"displayModeBar": False}, style={"height": "300px", "marginTop": "16px"}),
                ],
            ),
        ]
    )


def register_daa_callbacks(app: dash.Dash) -> None:
    @app.callback(
        Output("daa-report-store", "data"),
        Output("daa-report-table", "data"),
        Output("daa-report-table", "columns"),
        Output("daa-report-chart", "figure"),
        Input("daa-generate", "n_clicks"),
        State("daa-report-type", "value"),
        State("daa-dc-filter", "value"),
        prevent_initial_call=True,
    )
    def _gen(_n, rtype, dc_filt):
        cols, rows = daa_report_rows(str(rtype or "summary"), dc_filt or None)
        df = pd.DataFrame(rows, columns=cols)
        data = df.to_dict("records")
        columns = [{"name": c, "id": c} for c in cols]
        fig = _report_figure(cols, rows)
        return {"columns": cols, "rows": rows}, data, columns, fig

    @app.callback(
        Output("daa-chat-log", "children"),
        Input("daa-chat-send", "n_clicks"),
        Input({"type": "daa-qa", "idx": ALL}, "n_clicks"),
        State("daa-chat-input", "value"),
        prevent_initial_call=True,
    )
    def _chat(send_n, _qa_ns, text):
        ctx = callback_context
        if not ctx.triggered:
            return no_update
        tid = ctx.triggered[0]["prop_id"].split(".")[0]
        reply_key = None
        user_line = (text or "").strip()
        if tid == "daa-chat-send":
            reply_key = match_scenario(user_line, "/daa") or "health_overview"
        else:
            import json

            try:
                obj = json.loads(tid)
                reply_key = obj.get("idx")
            except Exception:
                reply_key = "health_overview"
        ans = get_canned_answer(reply_key or "health_overview", "/daa")
        blocks = [
            dmc.Paper(
                p="xs",
                mb=6,
                withBorder=True,
                children=[dmc.Text("You", size="xs", c="dimmed", fw=600), dmc.Text(user_line or "(quick action)", size="sm")],
            )
            if tid == "daa-chat-send"
            else dmc.Paper(
                p="xs",
                mb=6,
                withBorder=True,
                children=[dmc.Text("Quick action", size="xs", c="dimmed", fw=600), dmc.Text(str(reply_key), size="sm")],
            ),
            dmc.Paper(
                p="sm",
                withBorder=True,
                bg="gray.0",
                children=[dmc.Text("DAA (mock)", size="xs", c="dimmed", fw=600), dmc.Text(ans, size="sm")],
            ),
        ]
        return blocks

    @app.callback(
        Output("daa-download-excel", "data"),
        Input("daa-export-xlsx", "n_clicks"),
        State("daa-report-store", "data"),
        State("app-time-range", "data"),
        prevent_initial_call=True,
    )
    def _xlsx(_n, store, tr):
        if not store:
            return no_update
        cols = store.get("columns") or []
        rows = store.get("rows") or []
        df = pd.DataFrame(rows, columns=cols)
        content = dataframes_to_excel_with_meta(
            {"DAA_Report": df},
            tr,
            "daa",
            extra_filters={"source": "mock"},
        )
        return dash_send_excel_workbook(content, "daa_report")

    @app.callback(
        Output("daa-download-csv", "data"),
        Input("daa-export-csv", "n_clicks"),
        State("daa-report-store", "data"),
        State("app-time-range", "data"),
        prevent_initial_call=True,
    )
    def _csv(_n, store, tr):
        if not store:
            return no_update
        cols = store.get("columns") or []
        rows = store.get("rows") or []
        df = pd.DataFrame(rows, columns=cols)
        meta = build_report_info_df(tr, "daa", {"source": "mock"})
        content = csv_bytes_with_report_header(meta, [("DAA_Report", df)])
        return dash_send_csv_bytes(content, "daa_report")
