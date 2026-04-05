"""Floating mock assistant (APP_MODE=mock only) — Sendbird-style window above sticky headers."""

from __future__ import annotations

import json
import random
import time
from datetime import datetime

import dash
import dash_mantine_components as dmc
from dash import ALL, Input, Output, State, callback_context, dcc, html, no_update
from dash_iconify import DashIconify

from src.services.mock_data.daa_scenarios import get_canned_answer, match_scenario, quick_actions_for_path

# Accent aligned with reference (purple + product indigo)
_ACCENT = "#742DDD"
_USER_BUBBLE = "#4318FF"
_BOT_BG = "#F0F0F3"


def _bubble_user(text: str) -> html.Div:
    return html.Div(
        style={"display": "flex", "justifyContent": "flex-end", "marginBottom": "10px", "width": "100%"},
        children=[
            html.Div(
                style={
                    "maxWidth": "85%",
                    "padding": "10px 14px",
                    "borderRadius": "16px 16px 4px 16px",
                    "backgroundColor": _USER_BUBBLE,
                    "color": "#fff",
                    "fontSize": "13px",
                    "lineHeight": 1.45,
                    "boxShadow": "0 1px 4px rgba(67,24,255,0.25)",
                },
                children=text,
            )
        ],
    )


def _bubble_bot(text: str) -> html.Div:
    return html.Div(
        style={
            "display": "flex",
            "justifyContent": "flex-start",
            "alignItems": "flex-start",
            "gap": "8px",
            "marginBottom": "10px",
            "width": "100%",
        },
        children=[
            html.Div(
                style={
                    "width": "28px",
                    "height": "28px",
                    "borderRadius": "50%",
                    "background": f"linear-gradient(135deg, {_ACCENT} 0%, {_USER_BUBBLE} 100%)",
                    "flexShrink": 0,
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center",
                },
                children=DashIconify(icon="solar:chat-round-dots-bold-duotone", width=16, color="white"),
            ),
            html.Div(
                style={
                    "maxWidth": "80%",
                    "padding": "10px 14px",
                    "borderRadius": "16px 16px 16px 4px",
                    "backgroundColor": _BOT_BG,
                    "color": "#2B3674",
                    "fontSize": "13px",
                    "lineHeight": 1.45,
                },
                children=text,
            ),
        ],
    )


def _date_separator() -> html.Div:
    label = datetime.now().strftime("%B %d, %Y")
    return html.Div(
        style={
            "display": "flex",
            "alignItems": "center",
            "gap": "12px",
            "margin": "12px 0 16px",
            "color": "#A3AED0",
            "fontSize": "11px",
        },
        children=[
            html.Div(style={"flex": 1, "height": "1px", "background": "#E9EDF7"}),
            label,
            html.Div(style={"flex": 1, "height": "1px", "background": "#E9EDF7"}),
        ],
    )


def _render_history(history: list | None) -> list:
    if not history:
        return [
            _date_separator(),
            html.Div(
                style={
                    "color": "#A3AED0",
                    "fontSize": "12px",
                    "textAlign": "center",
                    "padding": "24px 8px",
                },
                children="Ask a question or pick a quick action. Static demo responses only.",
            ),
        ]
    blocks = [_date_separator()]
    for m in history:
        role = m.get("role", "assistant")
        text = m.get("text", "")
        if role == "user":
            blocks.append(_bubble_user(text))
        else:
            blocks.append(_bubble_bot(text))
    return blocks


def _panel_style_dict(is_open: bool, expanded: bool) -> dict:
    return {
        "position": "absolute",
        "right": "0",
        "bottom": "72px",
        "width": "420px" if expanded else "380px",
        "maxHeight": "min(78vh, 620px)" if expanded else "min(72vh, 560px)",
        "display": "flex" if is_open else "none",
        "flexDirection": "column",
        "backgroundColor": "#FFFFFF",
        "borderRadius": "18px",
        "boxShadow": "0 12px 48px rgba(15, 23, 42, 0.18), 0 4px 16px rgba(67, 24, 255, 0.12)",
        "overflow": "hidden",
        "fontFamily": "'DM Sans', sans-serif",
        "border": "1px solid rgba(67, 24, 255, 0.12)",
    }


def build_mock_chatbot() -> html.Div:
    return html.Div(
        id="mock-chatbot-anchor",
        style={
            "position": "fixed",
            "right": "24px",
            "bottom": "24px",
            "zIndex": 20000,
        },
        children=[
            html.Div(id="mock-chatbot-scroll-dummy", style={"display": "none"}),
            dcc.Store(id="mock-chatbot-open", data=False),
            dcc.Store(id="mock-chatbot-history", data=[]),
            dcc.Store(id="mock-chatbot-expanded", data=False),
            html.Div(
                id="mock-chatbot-panel",
                style=_panel_style_dict(False, False),
                children=[
                    html.Div(
                        style={
                            "display": "flex",
                            "alignItems": "center",
                            "justifyContent": "space-between",
                            "padding": "12px 14px",
                            "background": "linear-gradient(90deg, #2B1B6E 0%, #4318FF 100%)",
                            "color": "#fff",
                            "borderBottom": "1px solid rgba(255,255,255,0.15)",
                            "flexShrink": 0,
                        },
                        children=[
                            html.Div(
                                style={"display": "flex", "alignItems": "center", "gap": "10px"},
                                children=[
                                    html.Div(
                                        style={
                                            "width": "32px",
                                            "height": "32px",
                                            "borderRadius": "50%",
                                            "background": "rgba(255,255,255,0.2)",
                                            "display": "flex",
                                            "alignItems": "center",
                                            "justifyContent": "center",
                                        },
                                        children=DashIconify(
                                            icon="solar:stars-minimalistic-bold-duotone", width=20, color="white"
                                        ),
                                    ),
                                    html.Div(
                                        children=[
                                            html.Div(
                                                "Datalake Assistant",
                                                style={"fontWeight": 700, "fontSize": "15px"},
                                            ),
                                            html.Div(
                                                "Uses this page as context (mock)",
                                                style={"fontSize": "10px", "opacity": 0.9},
                                            ),
                                        ]
                                    ),
                                ],
                            ),
                            html.Div(
                                style={"display": "flex", "gap": "2px"},
                                children=[
                                    dmc.ActionIcon(
                                        DashIconify(icon="solar:refresh-bold", width=18, color="white"),
                                        id="mock-chatbot-refresh",
                                        variant="transparent",
                                        size="md",
                                        style={"color": "white"},
                                    ),
                                    dmc.ActionIcon(
                                        DashIconify(icon="solar:maximize-square-bold", width=18, color="white"),
                                        id="mock-chatbot-expand",
                                        variant="transparent",
                                        size="md",
                                        style={"color": "white"},
                                    ),
                                    dmc.ActionIcon(
                                        DashIconify(icon="solar:close-circle-bold", width=20, color="white"),
                                        id="mock-chatbot-close",
                                        variant="transparent",
                                        size="md",
                                        style={"color": "white"},
                                    ),
                                ],
                            ),
                        ],
                    ),
                    html.Div(
                        style={
                            "padding": "10px 14px 0",
                            "flex": 1,
                            "minHeight": 0,
                            "display": "flex",
                            "flexDirection": "column",
                        },
                        children=[
                            html.Div(
                                id="mock-chatbot-messages",
                                style={
                                    "flex": 1,
                                    "overflowY": "auto",
                                    "minHeight": "160px",
                                    "maxHeight": "280px",
                                    "paddingRight": "4px",
                                },
                                children=_render_history([]),
                            ),
                            html.Div(
                                id="mock-chatbot-quick",
                                style={"marginTop": "10px", "marginBottom": "8px"},
                            ),
                            html.Div(
                                style={
                                    "display": "flex",
                                    "gap": "8px",
                                    "alignItems": "center",
                                    "paddingBottom": "12px",
                                },
                                children=[
                                    dmc.TextInput(
                                        id="mock-chatbot-input",
                                        placeholder="Ask about this page…",
                                        style={"flex": 1},
                                        radius="md",
                                    ),
                                    dmc.ActionIcon(
                                        DashIconify(icon="solar:plain-bold", width=22, color="white"),
                                        id="mock-chatbot-send",
                                        size="xl",
                                        radius="xl",
                                        variant="filled",
                                        color="violet",
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
            dmc.ActionIcon(
                DashIconify(icon="solar:chat-round-dots-bold-duotone", width=26),
                id="mock-chatbot-toggle",
                size="xl",
                radius="xl",
                variant="filled",
                color="violet",
                style={
                    "boxShadow": "0 8px 24px rgba(116,45,221,0.4)",
                    "position": "relative",
                    "zIndex": 1,
                },
            ),
        ],
    )


def register_mock_chatbot_callbacks(app: dash.Dash) -> None:
    @app.callback(
        Output("mock-chatbot-open", "data"),
        Input("mock-chatbot-toggle", "n_clicks"),
        Input("mock-chatbot-close", "n_clicks"),
        State("mock-chatbot-open", "data"),
        prevent_initial_call=True,
    )
    def _toggle_open(_t, _c, is_open):
        ctx = callback_context
        tid = (ctx.triggered[0]["prop_id"] or "").split(".")[0]
        cur = bool(is_open)
        if tid == "mock-chatbot-close":
            return False
        return not cur

    @app.callback(
        Output("mock-chatbot-panel", "style"),
        Input("mock-chatbot-open", "data"),
        Input("mock-chatbot-expanded", "data"),
    )
    def _panel_style(is_open, expanded):
        return _panel_style_dict(bool(is_open), bool(expanded))

    @app.callback(
        Output("mock-chatbot-expanded", "data"),
        Input("mock-chatbot-expand", "n_clicks"),
        State("mock-chatbot-expanded", "data"),
        prevent_initial_call=True,
    )
    def _expand(_n, cur):
        return not bool(cur)

    @app.callback(Output("mock-chatbot-quick", "children"), Input("url", "pathname"))
    def _quick(pathname):
        actions = quick_actions_for_path(pathname or "/")
        return html.Div(
            children=[
                html.Div(
                    "Quick actions",
                    style={
                        "fontSize": "11px",
                        "fontWeight": 600,
                        "color": "#A3AED0",
                        "marginBottom": "6px",
                    },
                ),
                html.Div(
                    style={"display": "flex", "flexWrap": "wrap", "gap": "6px"},
                    children=[
                        dmc.Button(
                            a["label"],
                            id={"type": "mock-chat-qa", "idx": a["id"]},
                            size="xs",
                            variant="outline",
                            color="violet",
                            radius="xl",
                            styles={
                                "root": {
                                    "borderColor": _ACCENT,
                                    "color": _ACCENT,
                                    "fontWeight": 500,
                                }
                            },
                        )
                        for a in actions
                    ],
                ),
            ],
        )

    @app.callback(
        Output("mock-chatbot-history", "data"),
        Output("mock-chatbot-input", "value"),
        Input("mock-chatbot-send", "n_clicks"),
        Input({"type": "mock-chat-qa", "idx": ALL}, "n_clicks"),
        State("mock-chatbot-input", "value"),
        State("mock-chatbot-history", "data"),
        State("url", "pathname"),
        prevent_initial_call=True,
    )
    def _append_message(_send, _qa, text, history, pathname):
        ctx = callback_context
        if not ctx.triggered:
            return no_update, no_update
        raw = ctx.triggered[0]["prop_id"].rsplit(".", 1)[0]
        pathname = pathname or "/"
        hist = list(history or [])
        if raw == "mock-chatbot-send":
            key = match_scenario(text or "", pathname) or "health_overview"
            user = (text or "").strip() or "(empty message)"
            clear_input = ""
        else:
            try:
                key = json.loads(raw).get("idx", "health_overview")
            except Exception:
                key = "health_overview"
            actions = quick_actions_for_path(pathname)
            user = next(
                (a.get("user_text") or a.get("label", "") for a in actions if a.get("id") == key),
                "",
            ) or f"Tell me more about scenario {key}."
            clear_input = no_update
        time.sleep(random.uniform(0.6, 1.2))
        ans = get_canned_answer(key, pathname)
        hist.append({"role": "user", "text": user})
        hist.append({"role": "assistant", "text": ans})
        return hist, clear_input

    @app.callback(
        Output("mock-chatbot-history", "data", allow_duplicate=True),
        Input("mock-chatbot-refresh", "n_clicks"),
        prevent_initial_call=True,
    )
    def _clear_history(_n):
        return []

    @app.callback(
        Output("mock-chatbot-messages", "children"),
        Input("mock-chatbot-history", "data"),
        Input("url", "pathname"),
    )
    def _render_messages(history, _pathname):
        return _render_history(history)

