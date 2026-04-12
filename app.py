from __future__ import annotations
import json
import logging
import os
import time as time_module
from urllib.parse import parse_qs

import dash
import plotly.graph_objects as go
from dash import Dash, html, dcc, _dash_renderer, ALL
import dash_mantine_components as dmc
from dotenv import load_dotenv
from flask import request

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

from src.components.sidebar import create_sidebar_nav
from src.utils.branding import get_brand_title
from src.components.backup_panel import build_netbackup_panel, build_zerto_panel, build_veeam_panel
from src.components.charts import (
    create_capacity_area_chart,
    create_horizontal_bar_chart,
    create_usage_donut_chart,
)
from src.services import api_client as api
from src.services.db_service import DEFAULT_CUSTOMER_NAME, WARMED_CUSTOMERS
from src.utils.time_range import (
    PRESET_CUSTOM,
    default_time_range,
    preset_to_range,
    time_range_to_bounds,
)
from src.utils.format_units import pct_float, smart_storage
from src.components.s3_panel import build_dc_s3_panel, build_customer_s3_panel
from src.pages.home import _phys_inv_bar_figure

_dash_renderer._set_react_version("18.2.0")

stylesheets = [
    "https://unpkg.com/@mantine/core@7.10.0/styles.css",
    "https://unpkg.com/@mantine/dates@7.10.0/styles.css",
    "https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&display=swap",
]

app = Dash(
    __name__,
    use_pages=False,
    external_stylesheets=stylesheets,
    suppress_callback_exceptions=True,
    title=get_brand_title(),
)
server = app.server

APP_BUILD_ID = (os.environ.get("APP_BUILD_ID") or "dev").strip()


@server.after_request
def _prevent_stale_dash_cache(response):
    """Avoid browsers/CDNs serving an old Dash shell after a new image is deployed."""
    try:
        path = request.path
        ct = (response.content_type or "").lower()
        if path.startswith("/_dash") or "text/html" in ct:
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
    except Exception:
        pass
    return response


_log = logging.getLogger(__name__)
_log.info("APP_BUILD_ID=%s", APP_BUILD_ID)

from src.pages import home, datacenters, dc_view, customer_view, query_explorer, global_view, region_drilldown
from src.pages.settings import shell as settings_shell
from src.utils.app_mode import is_mock_mode
from src.pages.dc_view import _bps_to_gbps, _build_compute_tab

_default_tr = default_time_range()
_custom_st, _custom_en = time_range_to_bounds(_default_tr)
_custom_picker_start = _custom_st.strftime("%Y-%m-%dT%H:%M:%S")
_custom_picker_end = _custom_en.strftime("%Y-%m-%dT%H:%M:%S")
try:
    _customers = api.get_customer_list()
except Exception as exc:
    logging.getLogger(__name__).warning("get_customer_list failed at startup (using defaults): %s", exc)
    _customers = []
if not _customers:
    _customers = list(WARMED_CUSTOMERS)
_default_customer = _customers[0] if _customers else DEFAULT_CUSTOMER_NAME
_customer_options = [{"value": c, "label": c} for c in _customers]

_sidebar = html.Div(
    style={
        "width": "260px",
        "position": "fixed",
        "top": "16px",
        "left": "16px",
        "height": "calc(100vh - 32px)",
        "zIndex": 999,
        "padding": "24px",
        "backgroundColor": "#FFFFFF",
        "overflowY": "auto",
        "overflowX": "hidden",
        "borderRadius": "16px",
        "boxShadow": "0 10px 30px rgba(0, 0, 0, 0.08), 0 4px 12px rgba(0, 0, 0, 0.04)",
        "display": "flex",
        "flexDirection": "column",
    },
    children=[
        html.Div(id="sidebar-nav"),

        dmc.Stack(
            [
                dmc.Divider(mt="xl", style={"marginBottom": "4px"}),
                dmc.Text(
                    "REPORT PERIOD",
                    size="xs",
                    fw=600,
                    c="dimmed",
                    style={"letterSpacing": "0.06em"},
                ),
                dmc.SegmentedControl(
                    id="time-range-preset",
                    value=_default_tr.get("preset", "7d"),
                    data=[
                        {"label": "1H", "value": "1h"},
                        {"label": "1D", "value": "1d"},
                        {"label": "7D", "value": "7d"},
                        {"label": "30D", "value": "30d"},
                        {"label": "Cstm", "value": "custom"},
                    ],
                    size="sm",
                    fullWidth=True,
                ),
                html.Div(
                    id="time-range-custom-container",
                    children=[
                        dmc.Stack(
                            gap="xs",
                            children=[
                                dmc.Text("Start", size="xs", c="dimmed", fw=500),
                                dmc.DateTimePicker(
                                    id="time-range-start-datetime",
                                    value=_custom_picker_start,
                                    valueFormat="DD/MM/YYYY HH:mm",
                                    placeholder="Start",
                                    radius="md",
                                    size="sm",
                                    w="100%",
                                    popoverProps={"withinPortal": True, "zIndex": 9999},
                                ),
                                dmc.Text("End", size="xs", c="dimmed", fw=500),
                                dmc.DateTimePicker(
                                    id="time-range-end-datetime",
                                    value=_custom_picker_end,
                                    valueFormat="DD/MM/YYYY HH:mm",
                                    placeholder="End",
                                    radius="md",
                                    size="sm",
                                    w="100%",
                                    popoverProps={"withinPortal": True, "zIndex": 9999},
                                ),
                            ],
                        ),
                    ],
                    style={"position": "relative", "display": "none"},
                ),
            ],
            gap="xs",
            px="md",
            mt="auto",
        ),

        html.Div(
            id="customer-section",
            children=[
                dmc.Text("Customer", size="xs", fw=600, c="#A3AED0", style={"marginBottom": "6px"}),
                dmc.Select(
                    id="customer-select",
                    data=_customer_options,
                    value=_default_customer,
                    radius="md",
                    variant="default",
                    size="sm",
                    style={"width": "100%"},
                ),
            ],
            style={
                "marginTop": "16px",
                "paddingTop": "12px",
                "borderTop": "1px solid #E9ECEF",
                "display": "none",
            },
        ),
    ],
)

_mantine_children = [
    dcc.Location(id="url", refresh=False),
    html.Div(
        APP_BUILD_ID,
        id="app-deploy-revision",
        title="Deploy revision (env APP_BUILD_ID)",
        style={
            "position": "fixed",
            "bottom": "2px",
            "right": "8px",
            "fontSize": "10px",
            "color": "#ADB5BD",
            "zIndex": 9998,
            "pointerEvents": "none",
            "userSelect": "none",
        },
    ),
    dcc.Store(id="app-time-range", data=_default_tr),
    html.Div(id="export-pdf-clientside-dummy", style={"display": "none"}),
    # Always-mounted triggers for clientside PDF callback (page-visible buttons use data-pdf-target + assets/pdf_export_trigger.js).
    html.Div(
        [
            html.Button(
                id=hid,
                n_clicks=0,
                type="button",
                title="pdf-trigger",
                style={"display": "none"},
            )
            for hid in (
                "home-export-pdf",
                "datacenters-export-pdf",
                "dc-export-pdf",
                "global-export-pdf",
                "customer-export-pdf",
                "qe-export-pdf",
            )
        ],
        id="pdf-export-hidden-triggers",
        style={"display": "none"},
    ),
    html.Div(
        [
            _sidebar,
            html.Div(
                dcc.Loading(
                    id="main-content-loading",
                    type="circle",
                    color="#4318FF",
                    children=html.Div(id="main-content", children=[]),
                    style={"minHeight": "240px"},
                ),
                style={
                    "marginLeft": "292px",
                    "padding": "30px",
                    "minHeight": "100vh",
                    "width": "calc(100% - 292px)",
                    "backgroundColor": "#F4F7FE",
                },
            ),
        ],
        style={"display": "flex", "backgroundColor": "#F4F7FE", "minHeight": "100vh"},
    ),
]
if is_mock_mode():
    from src.components.chatbot import build_mock_chatbot

    _mantine_children.append(build_mock_chatbot())

app.layout = dmc.MantineProvider(
    theme={
        "fontFamily": "'DM Sans', sans-serif",
        "headings": {"fontFamily": "'DM Sans', sans-serif"},
        "primaryColor": "indigo",
    },
    children=_mantine_children,
)

if is_mock_mode():
    from src.components.chatbot import register_mock_chatbot_callbacks
    from src.pages.daa import register_daa_callbacks

    register_mock_chatbot_callbacks(app)
    register_daa_callbacks(app)

    app.clientside_callback(
        """
        function(children) {
            const el = document.getElementById("mock-chatbot-messages");
            if (!el) {
                return window.dash_clientside.no_update;
            }
            requestAnimationFrame(function() {
                el.scrollTop = el.scrollHeight;
            });
            return "";
        }
        """,
        dash.Output("mock-chatbot-scroll-dummy", "children"),
        dash.Input("mock-chatbot-messages", "children"),
    )


app.clientside_callback(
    """
    function(homePdf, dcListPdf, dcPdf, globalPdf, customerPdf, qePdf) {
        const triggered = dash_clientside.callback_context.triggered;
        if (!triggered || !triggered.length || !triggered[0]) {
            return window.dash_clientside.no_update;
        }
        const propId = triggered[0].prop_id || "";
        const id = propId.split(".")[0];
        const map = {
            "home-export-pdf": "home_overview",
            "datacenters-export-pdf": "datacenters",
            "dc-export-pdf": "dc_detail",
            "global-export-pdf": "global_view",
            "customer-export-pdf": "customer_view",
            "qe-export-pdf": "query_explorer"
        };
        const prefix = map[id];
        if (!prefix) {
            return window.dash_clientside.no_update;
        }
        const ts = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
        if (typeof window.triggerPagePDF === "function") {
            window.triggerPagePDF("main-content", prefix + "_" + ts + ".pdf");
        }
        return window.dash_clientside.no_update;
    }
    """,
    dash.Output("export-pdf-clientside-dummy", "children"),
    dash.Input("home-export-pdf", "n_clicks"),
    dash.Input("datacenters-export-pdf", "n_clicks"),
    dash.Input("dc-export-pdf", "n_clicks"),
    dash.Input("global-export-pdf", "n_clicks"),
    dash.Input("customer-export-pdf", "n_clicks"),
    dash.Input("qe-export-pdf", "n_clicks"),
    prevent_initial_call=True,
)


@app.callback(
    dash.Output("sidebar-nav", "children"),
    dash.Input("url", "pathname"),
)
def update_sidebar_nav(pathname):
    return create_sidebar_nav(pathname or "/")


@app.callback(
    dash.Output("customer-section", "style"),
    dash.Input("url", "pathname"),
)
def toggle_customer_section(pathname):
    base = {"marginTop": "16px", "paddingTop": "12px", "borderTop": "1px solid #E9ECEF"}
    if (pathname or "/") == "/customer-view":
        return {**base, "display": "block"}
    return {**base, "display": "none"}


def _normalize_custom_iso(v: str | None) -> str | None:
    if not v:
        return None
    s = str(v).strip()
    if s.endswith("Z"):
        return s
    if "+" in s[-6:] or s.endswith("UTC"):
        return s
    if "T" in s:
        return s + "Z"
    return s


@app.callback(
    dash.Output("time-range-custom-container", "style"),
    dash.Input("time-range-preset", "value"),
)
def toggle_custom_time_container(preset):
    base = {"position": "relative"}
    if preset == PRESET_CUSTOM:
        return {**base, "display": "block"}
    return {**base, "display": "none"}


@app.callback(
    dash.Output("time-range-start-datetime", "value"),
    dash.Output("time-range-end-datetime", "value"),
    dash.Input("time-range-preset", "value"),
    dash.State("app-time-range", "data"),
)
def sync_custom_datetime_pickers(preset, store):
    if preset != PRESET_CUSTOM:
        return dash.no_update, dash.no_update
    tr = store or default_time_range()
    st, en = time_range_to_bounds(tr)
    return st.strftime("%Y-%m-%dT%H:%M:%S"), en.strftime("%Y-%m-%dT%H:%M:%S")


@app.callback(
    dash.Output("app-time-range", "data"),
    dash.Input("time-range-preset", "value"),
    dash.Input("time-range-start-datetime", "value"),
    dash.Input("time-range-end-datetime", "value"),
    dash.State("app-time-range", "data"),
)
def update_time_range_store(preset, start_dt, end_dt, current):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update
    tid = ctx.triggered[0]["prop_id"].split(".")[0]
    if tid == "time-range-preset":
        if preset == PRESET_CUSTOM:
            cur = current or default_time_range()
            st, en = time_range_to_bounds(cur)
            return {
                "start": st.strftime("%Y-%m-%dT%H:%M:%S") + "Z",
                "end": en.strftime("%Y-%m-%dT%H:%M:%S") + "Z",
                "preset": PRESET_CUSTOM,
            }
        return preset_to_range(preset)
    if tid in ("time-range-start-datetime", "time-range-end-datetime"):
        if (current or {}).get("preset") != PRESET_CUSTOM:
            return dash.no_update
        s = start_dt or (current or {}).get("start")
        e = end_dt or (current or {}).get("end")
        s = _normalize_custom_iso(s) if isinstance(s, str) else s
        e = _normalize_custom_iso(e) if isinstance(e, str) else e
        if s and e:
            return {"start": s, "end": e, "preset": PRESET_CUSTOM}
        return dash.no_update
    return dash.no_update


@app.callback(
    dash.Output("main-content", "children"),
    dash.Input("url", "pathname"),
    dash.Input("app-time-range", "data"),
    dash.Input("customer-select", "value"),
    dash.State("url", "search"),
)
def render_main_content(pathname, time_range, selected_customer, search):
    pathname = pathname or "/"
    tr = time_range or default_time_range()
    if pathname in ("/", ""):
        return home.build_overview(tr)
    if pathname == "/datacenters":
        return datacenters.build_datacenters(tr)
    if pathname and pathname.startswith("/datacenter/"):
        dc_id = pathname.replace("/datacenter/", "").strip("/")
        return dc_view.build_dc_view(dc_id, tr)
    if pathname == "/global-view":
        return global_view.build_global_view(tr)
    if pathname == "/customer-view":
        return customer_view.build_customer_layout(tr, selected_customer)
    if pathname == "/query-explorer":
        return query_explorer.layout()
    if pathname == "/analytics":
        if is_mock_mode():
            from src.pages import analytics as analytics_page

            return analytics_page.build_analytics(tr)
        return home.build_overview(tr)
    if pathname == "/daa":
        if is_mock_mode():
            from src.pages import daa as daa_page

            return daa_page.build_daa_page(tr)
        return home.build_overview(tr)
    if pathname == "/region-drilldown":
        from urllib.parse import parse_qs
        params = parse_qs((search or "").lstrip("?"))
        region = params.get("region", [""])[0]
        return region_drilldown.build_region_drilldown(region, tr)
    if pathname.startswith("/settings"):
        return settings_shell.build_settings_page(pathname, search)
    return home.build_overview(tr)


@app.callback(
    dash.Output("s3-dc-metrics-panel", "children"),
    dash.Input("s3-dc-pool-selector", "value"),
    dash.Input("app-time-range", "data"),
    dash.State("url", "pathname"),
)
def update_s3_dc_panel(selected_pools, time_range, pathname):
    if not pathname or not pathname.startswith("/datacenter/"):
        return dash.no_update
    dc_id = pathname.replace("/datacenter/", "").strip("/")
    tr = time_range or default_time_range()
    s3_data = api.get_dc_s3_pools(dc_id, tr)
    if not s3_data.get("pools"):
        return html.Div()
    pools = s3_data.get("pools") or []
    if not selected_pools:
        selected = pools
    else:
        selected = [p for p in selected_pools if p in pools] or pools
    return build_dc_s3_panel(dc_id, s3_data, tr, selected)


@app.callback(
    dash.Output("s3-customer-metrics-panel", "children"),
    dash.Input("s3-customer-vault-selector", "value"),
    dash.Input("app-time-range", "data"),
    dash.State("customer-select", "value"),
)
def update_s3_customer_panel(selected_vaults, time_range, customer_name):
    name = customer_name or DEFAULT_CUSTOMER_NAME
    tr = time_range or default_time_range()
    s3_data = api.get_customer_s3_vaults(name, tr)
    if not s3_data.get("vaults"):
        return html.Div()
    vaults = s3_data.get("vaults") or []
    if not selected_vaults:
        selected = vaults
    else:
        selected = [v for v in selected_vaults if v in vaults] or vaults
    return build_customer_s3_panel(name, s3_data, tr, selected)


@app.callback(
    dash.Output("classic-virt-panel", "children"),
    dash.Input("virt-classic-cluster-selector", "value"),
    dash.Input("app-time-range", "data"),
    dash.State("url", "pathname"),
)
def update_classic_virt_panel(selected_clusters, time_range, pathname):
    if not pathname or not pathname.startswith("/datacenter/"):
        return dash.no_update
    dc_id = pathname.replace("/datacenter/", "").strip("/")
    tr = time_range or default_time_range()
    classic = api.get_classic_metrics_filtered(dc_id, selected_clusters, tr)
    return _build_compute_tab(classic, "Classic Compute", color="blue")


@app.callback(
    dash.Output("hyperconv-virt-panel", "children"),
    dash.Input("virt-hyperconv-cluster-selector", "value"),
    dash.Input("app-time-range", "data"),
    dash.State("url", "pathname"),
)
def update_hyperconv_virt_panel(selected_clusters, time_range, pathname):
    if not pathname or not pathname.startswith("/datacenter/"):
        return dash.no_update
    dc_id = pathname.replace("/datacenter/", "").strip("/")
    tr = time_range or default_time_range()
    hyperconv = api.get_hyperconv_metrics_filtered(dc_id, selected_clusters, tr)
    return _build_compute_tab(hyperconv, "Hyperconverged Compute", color="teal")


@app.callback(
    dash.Output("backup-netbackup-panel", "children"),
    dash.Input("backup-nb-pool-selector", "value"),
    dash.Input("app-time-range", "data"),
    dash.State("url", "pathname"),
)
def update_backup_netbackup_panel(selected_pools, time_range, pathname):
    if not pathname or not pathname.startswith("/datacenter/"):
        return dash.no_update
    dc_id = pathname.replace("/datacenter/", "").strip("/")
    tr = time_range or default_time_range()
    data = api.get_dc_netbackup_pools(dc_id, tr)
    pools = data.get("pools") or []
    if not pools:
        return html.Div()
    if not selected_pools:
        selected = pools
    else:
        selected = [p for p in selected_pools if p in pools] or pools
    return build_netbackup_panel(data, selected)


@app.callback(
    dash.Output("backup-zerto-panel", "children"),
    dash.Input("backup-zerto-site-selector", "value"),
    dash.Input("app-time-range", "data"),
    dash.State("url", "pathname"),
)
def update_backup_zerto_panel(selected_sites, time_range, pathname):
    if not pathname or not pathname.startswith("/datacenter/"):
        return dash.no_update
    dc_id = pathname.replace("/datacenter/", "").strip("/")
    tr = time_range or default_time_range()
    data = api.get_dc_zerto_sites(dc_id, tr)
    sites = data.get("sites") or []
    if not sites:
        return html.Div()
    if not selected_sites:
        selected = sites
    else:
        selected = [s for s in selected_sites if s in sites] or sites
    return build_zerto_panel(data, selected)


@app.callback(
    dash.Output("backup-veeam-panel", "children"),
    dash.Input("backup-veeam-repo-selector", "value"),
    dash.Input("app-time-range", "data"),
    dash.State("url", "pathname"),
)
def update_backup_veeam_panel(selected_repos, time_range, pathname):
    if not pathname or not pathname.startswith("/datacenter/"):
        return dash.no_update
    dc_id = pathname.replace("/datacenter/", "").strip("/")
    tr = time_range or default_time_range()
    data = api.get_dc_veeam_repos(dc_id, tr)
    repos = data.get("repos") or []
    if not repos:
        return html.Div()
    if not selected_repos:
        selected = repos
    else:
        selected = [r for r in selected_repos if r in repos] or repos
    return build_veeam_panel(data, selected)


@app.callback(
    dash.Output("phys-inv-overview-chart", "figure"),
    dash.Output("phys-inv-overview-chart", "style"),
    dash.Output("phys-inv-drill-state", "data"),
    dash.Output("phys-inv-reset-btn", "style"),
    dash.Input("phys-inv-overview-chart", "clickData"),
    dash.Input("phys-inv-reset-btn", "n_clicks"),
    dash.State("phys-inv-drill-state", "data"),
    prevent_initial_call=True,
)
def update_phys_inv_chart(click_data, reset_clicks, state):
    state = state or {"level": 0, "role": None, "manufacturer": None}
    level = state.get("level", 0)
    role = state.get("role")
    manufacturer = state.get("manufacturer")

    def chart_height(n):
        return max(260, min(520, n * 32))

    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update
    trigger_id = ctx.triggered[0]["prop_id"]
    triggered_by_reset = "phys-inv-reset-btn" in trigger_id

    if triggered_by_reset:
        data = api.get_physical_inventory_overview_by_role()
        labels = [r["role"] for r in data]
        counts = [r["count"] for r in data]
        h = chart_height(len(labels))
        fig = _phys_inv_bar_figure(labels, counts, height=h)
        new_state = {"level": 0, "role": None, "manufacturer": None}
        return fig, {"height": f"{h}px"}, new_state, {"display": "none"}

    if not click_data or "points" not in click_data or not click_data["points"]:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update

    clicked_label = click_data["points"][0].get("y")
    if clicked_label is None:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update

    if level == 0:
        data = api.get_physical_inventory_overview_manufacturer(clicked_label)
        labels = [r["manufacturer"] for r in data]
        counts = [r["count"] for r in data]
        h = chart_height(len(labels))
        fig = _phys_inv_bar_figure(labels, counts, height=h)
        new_state = {"level": 1, "role": clicked_label, "manufacturer": None}
        return fig, {"height": f"{h}px"}, new_state, {"display": "inline-block"}
    if level == 1:
        data = api.get_physical_inventory_overview_location(role or "", clicked_label)
        labels = [r["location"] for r in data]
        counts = [r["count"] for r in data]
        h = chart_height(len(labels))
        fig = _phys_inv_bar_figure(labels, counts, height=h)
        new_state = {"level": 2, "role": role, "manufacturer": clicked_label}
        return fig, {"height": f"{h}px"}, new_state, {"display": "inline-block"}
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update


# ---------------------------------------------------------------------------
# Global View — DashGlobe callbacks
# ---------------------------------------------------------------------------


@app.callback(
    dash.Output("global-detail-panel", "children"),
    dash.Output("last-clicked-dc-id", "data"),
    dash.Output("current-view-mode", "data", allow_duplicate=True),
    dash.Output("selected-building-dc-store", "data"),
    dash.Input("global-map-graph", "clickedPoint"),
    dash.State("last-clicked-dc-id", "data"),
    dash.State("app-time-range", "data"),
    prevent_initial_call=True,
)
def handle_globe_pin_click(clicked_point, last_dc_id, time_range):
    if not clicked_point:
        return [], None, dash.no_update, dash.no_update
    dc_id = clicked_point.get("dc_id")
    site_name = clicked_point.get("site_name", "")
    if not dc_id:
        return [], None, dash.no_update, dash.no_update
    # Double-click same pin → building reveal mode
    if dc_id == last_dc_id:
        return dash.no_update, dc_id, "building", {"dc_id": dc_id, "dc_name": dc_id}
    # First click → show DC info card
    tr = time_range or default_time_range()
    from src.pages.global_view import build_dc_info_card
    panel = build_dc_info_card(dc_id, tr, site_name=site_name)
    return panel, dc_id, dash.no_update, dash.no_update


@app.callback(
    dash.Output("global-3d-modal-container", "children"),
    dash.Output("global-3d-modal-container", "style"),
    dash.Input({"type": "open-3d-hologram-btn", "index": ALL}, "n_clicks"),
    dash.State("global-3d-modal-container", "style"),
    prevent_initial_call=True,
)
def open_3d_hologram_modal(btn_clicks, current_style):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update
    if all(x is None for x in btn_clicks):
        return dash.no_update, dash.no_update
    trig = ctx.triggered[0]["prop_id"].split(".")[0]
    try:
        trig_dict = json.loads(trig)
    except Exception:
        return dash.no_update, dash.no_update
    dc_id = trig_dict.get("index")
    if not dc_id:
        return dash.no_update, dash.no_update
    info = api.get_dc_details(dc_id, default_time_range())
    dc_name = info.get("meta", {}).get("name", dc_id)
    racks_resp = api.get_dc_racks(dc_id)
    racks = racks_resp.get("racks", [])
    if racks:
        from src.pages.global_view import build_3d_rack_overlay
        content = build_3d_rack_overlay(dc_id, dc_name, racks)
        new_style = dict(current_style) if current_style else {}
        new_style["display"] = "flex"
        new_style["pointerEvents"] = "auto"
        return content, new_style
    return [], current_style


@app.callback(
    dash.Output("global-3d-modal-container", "style", allow_duplicate=True),
    dash.Input("close-3d-overlay-btn", "n_clicks"),
    dash.State("global-3d-modal-container", "style"),
    prevent_initial_call=True,
)
def close_3d_hologram_modal(n_clicks, current_style):
    if not n_clicks:
        return dash.no_update
    new_style = dict(current_style) if current_style else {}
    new_style["display"] = "none"
    new_style["pointerEvents"] = "none"
    return new_style


@app.callback(
    dash.Output("globe-layer", "style"),
    dash.Output("building-reveal-layer", "style"),
    dash.Output("floor-map-layer", "style"),
    dash.Output("building-reveal-timer", "disabled"),
    dash.Output("building-reveal-timer", "n_intervals"),
    dash.Output("building-reveal-dc-name", "children"),
    dash.Input("current-view-mode", "data"),
    dash.State("selected-building-dc-store", "data"),
    prevent_initial_call=True,
)
def view_controller(mode, dc_store):
    shown = {"display": "block"}
    hidden = {"display": "none"}
    reveal_shown = {"display": "flex"}
    dc_label = (dc_store or {}).get("dc_name", "")
    if mode == "building":
        return hidden, reveal_shown, hidden, False, 0, dc_label
    if mode == "floor_map":
        return hidden, hidden, shown, True, dash.no_update, dc_label
    # Default: globe
    return shown, hidden, hidden, True, dash.no_update, dc_label


@app.callback(
    dash.Output("current-view-mode", "data", allow_duplicate=True),
    dash.Output("floor-map-layer", "children"),
    dash.Input("building-reveal-timer", "n_intervals"),
    dash.State("selected-building-dc-store", "data"),
    dash.State("current-view-mode", "data"),
    prevent_initial_call=True,
)
def advance_to_floor_map(n_intervals, dc_store, current_mode):
    if not n_intervals or current_mode != "building" or not dc_store:
        return dash.no_update, dash.no_update
    dc_id = dc_store.get("dc_id", "")
    dc_name = dc_store.get("dc_name", dc_id)
    racks_resp = api.get_dc_racks(dc_id)
    racks = racks_resp.get("racks", [])
    from src.pages.floor_map import build_floor_map_layout
    return "floor_map", build_floor_map_layout(dc_id, dc_name, racks)


@app.callback(
    dash.Output("current-view-mode", "data", allow_duplicate=True),
    dash.Output("last-clicked-dc-id", "data", allow_duplicate=True),
    dash.Input("back-to-global-btn", "n_clicks"),
    prevent_initial_call=True,
)
def back_to_globe(n_clicks):
    if not n_clicks:
        return dash.no_update, dash.no_update
    return "globe", None


@app.callback(
    dash.Output("floor-map-rack-detail", "children"),
    dash.Input("floor-map-graph", "clickData"),
    dash.State("selected-building-dc-store", "data"),
    prevent_initial_call=True,
)
def show_rack_detail(click_data, dc_store):
    if not click_data or "points" not in click_data or not click_data["points"]:
        return dash.no_update
    point = click_data["points"][0]
    custom = point.get("customdata")
    if not custom or not custom[0]:
        return dash.no_update
    dc_id = custom[0][0] if isinstance(custom[0], list) else custom[0]
    rack_name = custom[0][1] if isinstance(custom[0], list) else (custom[1] if len(custom) > 1 else "")
    status = custom[0][2] if isinstance(custom[0], list) else (custom[2] if len(custom) > 2 else "unknown")
    u_height = custom[0][3] if isinstance(custom[0], list) else (custom[3] if len(custom) > 3 else 42)
    energy = custom[0][4] if isinstance(custom[0], list) else (custom[4] if len(custom) > 4 else "?")
    rack_type = custom[0][5] if isinstance(custom[0], list) else (custom[5] if len(custom) > 5 else "")

    try:
        u_height = int(u_height)
    except (ValueError, TypeError):
        u_height = 42

    from src.services import api_client as _api
    devices_resp = _api.get_rack_devices(dc_id, rack_name)
    devices = devices_resp.get("devices", [])

    status_color = {
        "active": "#17B26A", "planned": "#2E90FA",
        "inactive": "#F04438", "unknown": "#98A2B3",
    }.get((status or "unknown").lower(), "#98A2B3")

    from dash import html as _html
    import dash_mantine_components as _dmc
    from dash_iconify import DashIconify as _DI

    unit_slots = []
    occupied: dict[int, dict] = {}
    for dev in devices:
        slot = dev.get("slot_start", 1) or 1
        occupied[slot] = dev

    for u in range(u_height, 0, -1):
        dev = occupied.get(u)
        if dev:
            spans = max(1, dev.get("u_size", 1) or 1)
            dev_color = "#EEF4FF"
            dev_border = "#C7D7FE"
            label = dev.get("name") or dev.get("type", f"Device @U{u}")
            unit_slots.append(
                _html.Div(
                    style={
                        "height": f"{spans * 20}px",
                        "background": dev_color,
                        "border": f"1px solid {dev_border}",
                        "borderRadius": "3px",
                        "marginBottom": "2px",
                        "display": "flex",
                        "alignItems": "center",
                        "padding": "0 6px",
                        "fontSize": "10px",
                        "fontWeight": 600,
                        "color": "#3538CD",
                        "overflow": "hidden",
                        "whiteSpace": "nowrap",
                    },
                    children=f"U{u} — {label}",
                )
            )
        else:
            unit_slots.append(
                _html.Div(
                    style={
                        "height": "20px",
                        "background": "#1E293B",
                        "border": "1px solid #2D3748",
                        "borderRadius": "2px",
                        "marginBottom": "2px",
                        "display": "flex",
                        "alignItems": "center",
                        "padding": "0 6px",
                        "fontSize": "9px",
                        "color": "#475569",
                    },
                    children=f"U{u}",
                )
            )

    return _html.Div([
        # Status bar
        _html.Div(
            style={"height": "4px", "background": status_color, "borderRadius": "4px 4px 0 0"},
        ),
        _html.Div(
            style={"padding": "16px"},
            children=[
                # Header
                _dmc.Group(
                    gap="sm",
                    mb="md",
                    children=[
                        _dmc.ThemeIcon(
                            _DI(icon="solar:server-bold-duotone", width=18),
                            size="lg", radius="md", color="indigo", variant="light",
                        ),
                        _html.Div([
                            _dmc.Text(rack_name or "Rack", fw=700, size="md", c="#1B2559"),
                            _dmc.Text(f"{dc_id} · {rack_type}", size="xs", c="#A3AED0"),
                        ]),
                        _dmc.Badge(
                            (status or "unknown").title(),
                            color={"active": "teal", "planned": "blue", "inactive": "red"}.get(
                                (status or "").lower(), "gray"
                            ),
                            variant="light", size="sm", ml="auto",
                        ),
                    ],
                ),
                # Quick stats
                _dmc.SimpleGrid(
                    cols=2, spacing="xs", mb="md",
                    children=[
                        _dmc.Paper(
                            p="xs", radius="md", withBorder=True,
                            children=[
                                _dmc.Text("U Height", size="xs", c="#A3AED0"),
                                _dmc.Text(f"{u_height}U", fw=700, size="lg", c="#1B2559"),
                            ],
                        ),
                        _dmc.Paper(
                            p="xs", radius="md", withBorder=True,
                            children=[
                                _dmc.Text("Power", size="xs", c="#A3AED0"),
                                _dmc.Text(f"{energy} kW", fw=700, size="lg", c="#1B2559"),
                            ],
                        ),
                    ],
                ),
                # Rack diagram
                _dmc.Text("Rack Units", size="xs", fw=600, c="#344054", mb="xs"),
                _html.Div(
                    className="rack-unit-cabinet",
                    children=[
                        _html.Div(className="rack-rail"),
                        _html.Div(
                            style={"flex": 1, "padding": "4px 6px", "overflowY": "auto"},
                            children=unit_slots,
                        ),
                        _html.Div(className="rack-rail rack-rail-right"),
                    ],
                ),
                _dmc.Text(
                    f"{len(devices)} device(s) installed",
                    size="xs", c="#A3AED0", mt="xs", ta="right",
                ),
            ],
        ),
    ])


@app.callback(
    dash.Output("global-detail-panel", "children", allow_duplicate=True),
    dash.Output("global-map-graph", "focusRegion", allow_duplicate=True),
    dash.Input("global-map-reset-btn", "n_clicks"),
    prevent_initial_call=True,
)
def reset_global_detail(n_clicks):
    if not n_clicks:
        return dash.no_update, dash.no_update
    return [], {"lat": 38.0, "lng": 30.0, "zoom": 3}


@app.callback(
    dash.Output("selected-region-store", "data"),
    dash.Input({"type": "region-nav", "region": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def update_region_store(n_clicks_list):
    import time as _time
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update
    triggered = ctx.triggered[0]
    if not triggered.get("value"):
        return dash.no_update
    prop_id = json.loads(triggered["prop_id"].rsplit(".", 1)[0])
    region = prop_id.get("region", "")
    from src.pages.global_view import REGION_ZOOM_TARGETS
    target = REGION_ZOOM_TARGETS.get(region, {})
    if not target:
        return dash.no_update
    return {
        "region": region,
        "lon": target["lon"],
        "lat": target["lat"],
        "scale": target["scale"],
        "ts": _time.time(),
    }


@app.callback(
    dash.Output("global-map-graph", "focusRegion"),
    dash.Input("selected-region-store", "data"),
    prevent_initial_call=True,
)
def update_globe_camera(region):
    if not region:
        return dash.no_update
    lat = region.get("lat")
    lng = region.get("lon")
    scale = region.get("scale", 6.0)
    if scale >= 35:
        zoom = 10
    elif scale >= 10:
        zoom = 8
    else:
        zoom = 5
    if lat is not None and lng is not None:
        return {"lat": float(lat), "lng": float(lng), "zoom": zoom}
    return dash.no_update


@app.callback(
    dash.Output("global-detail-panel", "children", allow_duplicate=True),
    dash.Input("selected-region-store", "data"),
    dash.State("app-time-range", "data"),
    prevent_initial_call=True,
)
def update_global_detail_from_menu(store_data, time_range):
    if not store_data or not store_data.get("region"):
        return dash.no_update
    region = store_data["region"]
    tr = time_range or default_time_range()
    from src.pages.global_view import build_region_detail_panel
    return build_region_detail_panel(region, tr)


# ---------------------------------------------------------------------------
# Network Dashboard (Zabbix) callbacks
# ---------------------------------------------------------------------------


@app.callback(
    dash.Output("net-role-selector", "data"),
    dash.Output("net-role-selector", "value"),
    dash.Output("net-device-selector", "data"),
    dash.Output("net-device-selector", "value"),
    dash.Input("net-manufacturer-selector", "value"),
    dash.Input("net-role-selector", "value"),
    dash.Input("net-filters-store", "data"),
)
def update_net_selectors(manufacturer, role, net_filters):
    """Single callback for role + device dropdowns (avoids duplicate Output writers)."""
    net_filters = net_filters or {}
    roles_by_manu = net_filters.get("roles_by_manufacturer") or {}
    devices_by_manu_role = net_filters.get("devices_by_manufacturer_role") or {}

    if not roles_by_manu:
        return [], None, [], None

    if manufacturer:
        roles = sorted(roles_by_manu.get(manufacturer) or [])
        devs_set: set = set()
        for r in roles:
            devs_set.update(devices_by_manu_role.get(manufacturer, {}).get(r, []) or [])
        devices_all = sorted(devs_set)
    else:
        roles = sorted({r for rs in roles_by_manu.values() for r in (rs or [])})
        devices_all = sorted(
            d
            for rm in devices_by_manu_role.values()
            for devs in rm.values()
            for d in (devs or [])
        )

    role_data = [{"label": r, "value": r} for r in roles]
    ctx = dash.callback_context
    triggered_id = getattr(ctx, "triggered_id", None)
    if triggered_id is None and ctx.triggered:
        triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if triggered_id == "net-role-selector":
        if manufacturer and role:
            devices = devices_by_manu_role.get(manufacturer, {}).get(role, []) or []
        elif manufacturer and not role:
            devices = []
            for r in roles_by_manu.get(manufacturer, []) or []:
                devices.extend(devices_by_manu_role.get(manufacturer, {}).get(r, []) or [])
        elif not manufacturer and role:
            devs = set()
            for roles_map in devices_by_manu_role.values():
                devs.update(roles_map.get(role, []) or [])
            devices = sorted(devs)
        else:
            devices = devices_all
        device_data = [{"label": d, "value": d} for d in sorted(devices or [])]
        return role_data, dash.no_update, device_data, None

    device_data = [{"label": d, "value": d} for d in devices_all]
    return role_data, None, device_data, None


@app.callback(
    dash.Output("net-kpi-container", "children"),
    dash.Output("net-donut-active-ports", "figure"),
    dash.Output("net-donut-utilization", "figure"),
    dash.Output("net-donut-icmp", "figure"),
    dash.Output("net-top-interfaces-bar", "figure"),
    dash.Input("net-manufacturer-selector", "value"),
    dash.Input("net-role-selector", "value"),
    dash.Input("net-device-selector", "value"),
    dash.Input("app-time-range", "data"),
    dash.State("url", "pathname"),
)
def update_net_kpis_and_charts(manufacturer, device_role, device_name, time_range, pathname):
    if not pathname or not pathname.startswith("/datacenter/"):
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    dc_id = pathname.replace("/datacenter/", "").strip("/")
    tr = time_range or default_time_range()

    port_summary = api.get_dc_network_port_summary(
        dc_id,
        tr,
        manufacturer=manufacturer,
        device_role=device_role,
        device_name=device_name,
    )
    percentile_data = api.get_dc_network_95th_percentile(
        dc_id,
        tr,
        top_n=20,
        manufacturer=manufacturer,
        device_role=device_role,
        device_name=device_name,
    )

    device_count = int(port_summary.get("device_count", 0) or 0)
    total_ports = int(port_summary.get("total_ports", 0) or 0)
    active_ports = int(port_summary.get("active_ports", 0) or 0)
    avg_icmp_loss_pct = float(port_summary.get("avg_icmp_loss_pct", 0) or 0)

    port_availability_pct = pct_float(active_ports, total_ports)
    icmp_availability_pct = max(0.0, min(100.0, 100.0 - avg_icmp_loss_pct))
    overall_util_pct = float(percentile_data.get("overall_port_utilization_pct", 0) or 0)

    kpis = dmc.SimpleGrid(
        cols=4,
        spacing="lg",
        children=[
            dc_view._kpi("Total Devices", f"{device_count:,}", "solar:server-bold-duotone", color="indigo"),
            dc_view._kpi("Active Ports", f"{active_ports:,}", "solar:signal-bold-duotone", color="indigo"),
            dc_view._kpi("Total Ports", f"{total_ports:,}", "solar:port-bold-duotone", color="indigo"),
            dc_view._kpi("Port Availability", f"{port_availability_pct:.1f}%", "solar:graph-bold-duotone", color="indigo"),
        ],
    )

    donut_active = create_usage_donut_chart(port_availability_pct, "Port Availability", color="#FFB547")
    donut_util = create_usage_donut_chart(overall_util_pct, "Port Utilization", color="#05CD99")
    donut_icmp = create_usage_donut_chart(icmp_availability_pct, "ICMP Availability", color="#4318FF")

    top_interfaces = percentile_data.get("top_interfaces") or []
    bar_labels = [(t.get("interface_name") or "").strip() or "Unknown" for t in top_interfaces]
    bar_values = [_bps_to_gbps(t.get("p95_total_bps")) for t in top_interfaces]
    bar_fig = create_horizontal_bar_chart(
        labels=bar_labels,
        values=bar_values,
        title="Top 95th Percentile Interfaces (Gbps)",
        color="#4318FF",
        height=320,
    )

    return kpis, donut_active, donut_util, donut_icmp, bar_fig


@app.callback(
    dash.Output("net-interface-table", "data"),
    dash.Input("net-manufacturer-selector", "value"),
    dash.Input("net-role-selector", "value"),
    dash.Input("net-device-selector", "value"),
    dash.Input("net-interface-search", "value"),
    dash.Input("net-interface-table", "page_current"),
    dash.Input("net-interface-table", "page_size"),
    dash.Input("app-time-range", "data"),
    dash.State("url", "pathname"),
)
def update_net_interface_table(manufacturer, device_role, device_name, search_value, page_current, page_size, time_range, pathname):
    if not pathname or not pathname.startswith("/datacenter/"):
        return []

    dc_id = pathname.replace("/datacenter/", "").strip("/")
    tr = time_range or default_time_range()

    page_current_safe = int(page_current or 0)
    page_size_safe = int(page_size or 50)
    page_backend = page_current_safe + 1  # backend is 1-based

    interface_data = api.get_dc_network_interface_table(
        dc_id,
        tr,
        page=page_backend,
        page_size=page_size_safe,
        search=search_value or "",
        manufacturer=manufacturer,
        device_role=device_role,
        device_name=device_name,
    )

    items = interface_data.get("items") or []
    rows = []
    for it in items:
        speed_gbps = (float(it.get("speed_bps") or 0) / 1e9) if it.get("speed_bps") is not None else 0.0
        total_gbps = (float(it.get("p95_total_bps") or 0) / 1e9) if it.get("p95_total_bps") is not None else 0.0
        rows.append(
            {
                "interface_name": it.get("interface_name") or "",
                "interface_alias": it.get("interface_alias") or "",
                "p95_total_gbps": round(total_gbps, 3),
                "speed_gbps": round(speed_gbps, 3),
                "utilization_pct": round(float(it.get("utilization_pct") or 0), 2),
            }
        )

    return rows


@app.callback(
    dash.Output("intel-donut-total", "figure"),
    dash.Output("intel-donut-used", "figure"),
    dash.Output("intel-donut-free", "figure"),
    dash.Output("intel-capacity-trend-chart", "figure"),
    dash.Input("intel-storage-device-selector", "value"),
    dash.Input("app-time-range", "data"),
    dash.State("url", "pathname"),
)
def update_intel_storage_charts(host, time_range, pathname):
    if not pathname or not pathname.startswith("/datacenter/"):
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update

    dc_id = pathname.replace("/datacenter/", "").strip("/")
    tr = time_range or default_time_range()

    cap = api.get_dc_zabbix_storage_capacity(dc_id, tr, host=host)
    trend = api.get_dc_zabbix_storage_trend(dc_id, tr, host=host)

    total_bytes = float(cap.get("total_capacity_bytes", 0) or 0)
    used_bytes = float(cap.get("used_capacity_bytes", 0) or 0)
    free_bytes = float(cap.get("free_capacity_bytes", 0) or 0)

    # Zabbix bytes -> GB for smart_storage labels.
    bytes_to_gb = lambda b: (float(b) / (1024.0**3)) if b else 0.0
    total_gb = bytes_to_gb(total_bytes)
    used_gb = bytes_to_gb(used_bytes)
    free_gb = bytes_to_gb(free_bytes)

    used_pct = pct_float(used_gb, total_gb)
    free_pct = max(0.0, 100.0 - used_pct)

    donut_total = create_usage_donut_chart(100.0, f"Total {smart_storage(total_gb)}", color="#FFB547")
    donut_used = create_usage_donut_chart(used_pct, "Used Capacity", color="#4318FF")
    donut_free = create_usage_donut_chart(free_pct, "Free Capacity", color="#05CD99")

    series = trend.get("series") or []
    timestamps = [p.get("ts") for p in series if p.get("ts") is not None]
    used_series = [p.get("used_capacity_bytes") for p in series]
    total_series = [p.get("total_capacity_bytes") for p in series]

    trend_fig = create_capacity_area_chart(
        timestamps=timestamps,
        used=used_series,
        total=total_series,
        title="Capacity Utilization Trend",
        height=260,
    )

    return donut_total, donut_used, donut_free, trend_fig


@app.callback(
    dash.Output("intel-disk-container", "children"),
    dash.Input("intel-storage-device-selector", "value"),
    dash.Input("app-time-range", "data"),
    dash.State("url", "pathname"),
)
def update_intel_disk_container(host, time_range, pathname):
    if not pathname or not pathname.startswith("/datacenter/"):
        return dash.no_update

    dc_id = pathname.replace("/datacenter/", "").strip("/")
    tr = time_range or default_time_range()

    if host is None:
        return [
            dmc.Text("Select a device to load disks.", size="sm", c="#A3AED0"),
            html.Div(id="intel-disk-trend-container"),
        ]

    disk_data = api.get_dc_zabbix_disk_list(dc_id, tr, host=host)
    disks = disk_data.get("items") or []
    disk_options = [{"label": d, "value": d} for d in disks]

    disk_selector = dmc.Select(
        id="intel-storage-disk-selector",
        data=disk_options,
        value=None,
        clearable=True,
        searchable=True,
        placeholder="Select disk",
        nothingFoundMessage="No disks",
        style={"minWidth": "260px"},
    )

    return [
        disk_selector,
        html.Div(id="intel-disk-trend-container"),
    ]


@app.callback(
    dash.Output("intel-disk-trend-container", "children"),
    dash.Input("intel-storage-disk-selector", "value"),
    dash.Input("intel-storage-device-selector", "value"),
    dash.Input("app-time-range", "data"),
    dash.State("url", "pathname"),
)
def update_intel_disk_trend(disk_name, host, time_range, pathname):
    if not pathname or not pathname.startswith("/datacenter/"):
        return dash.no_update

    if host is None or disk_name is None:
        return html.Div()

    dc_id = pathname.replace("/datacenter/", "").strip("/")
    tr = time_range or default_time_range()

    trend = api.get_dc_zabbix_disk_trend(dc_id, tr, host=host, disk_name=disk_name)
    series = trend.get("series") or []

    timestamps = [p.get("ts") for p in series if p.get("ts") is not None]
    iops_series = [float(p.get("avg_iops") or 0) for p in series]
    latency_series = [float(p.get("avg_latency_ms") or 0) for p in series]

    total_bytes_series = [float(p.get("total_capacity_bytes") or 0) for p in series]
    free_bytes_series = [float(p.get("free_capacity_bytes") or 0) for p in series]
    used_bytes_series = [t - f for t, f in zip(total_bytes_series, free_bytes_series)]

    capacity_fig = create_capacity_area_chart(
        timestamps=timestamps,
        used=used_bytes_series,
        total=total_bytes_series,
        title=f"Disk Capacity Utilization - {disk_name}",
        height=260,
    )

    iops_fig = go.Figure(data=[go.Scatter(x=timestamps, y=iops_series, mode="lines+markers", name="Avg IOPS")])
    iops_fig.update_layout(height=240, margin=dict(l=30, r=10, t=30, b=20))

    latency_fig = go.Figure(
        data=[go.Scatter(x=timestamps, y=latency_series, mode="lines+markers", name="Avg Latency (ms)")]
    )
    latency_fig.update_layout(height=240, margin=dict(l=30, r=10, t=30, b=20))

    return dmc.Stack(
        gap="lg",
        children=[
            html.Div(
                className="nexus-card",
                style={"padding": "20px"},
                children=[
                    dc_view._section_title("Disk Capacity Utilization", "Latest daily utilization trend"),
                    dc_view._chart_card(
                        dcc.Graph(
                            figure=capacity_fig,
                            config={"displayModeBar": False},
                            style={"height": "260px"},
                        )
                    ),
                ],
            ),
            html.Div(
                className="nexus-card",
                style={"padding": "20px"},
                children=[
                    dc_view._section_title("Disk Performance", "Avg IOPS and latency over time"),
                    dmc.SimpleGrid(
                        cols=2,
                        spacing="lg",
                        children=[
                            dc_view._chart_card(dcc.Graph(figure=iops_fig, config={"displayModeBar": False})),
                            dc_view._chart_card(dcc.Graph(figure=latency_fig, config={"displayModeBar": False})),
                        ],
                    ),
                ],
            ),
        ],
    )


if __name__ == "__main__":
    app.run(debug=True, dev_tools_ui=False, port=8050, use_reloader=False)
