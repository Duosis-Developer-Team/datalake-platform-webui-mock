"""
Floor Map Sub-Page — Plotly-based 2D top-down rack layout for a datacenter.
Renders hall zones with racks in a grid pattern.
"""

from __future__ import annotations

import plotly.graph_objects as go
from dash import html, dcc
import dash_mantine_components as dmc
from dash_iconify import DashIconify

# ── Layout constants ──────────────────────────────────────────────────────────
RACK_W       = 22
RACK_H       = 34
GAP_X        = 8
GAP_Y        = 10
AISLE_H      = 30
ZONE_PAD_X   = 22
ZONE_PAD_TOP = 14
ZONE_PAD_BOT = 14
ZONE_LABEL_H = 24
FLOOR_PAD    = 28
HALL_COL_GAP = 0
HALL_ROW_GAP = 0
HALLS_PER_ROW = 2

STATUS_FILL = {
    "active":   "#17B26A",
    "planned":  "#2E90FA",
    "inactive": "#F04438",
    "unknown":  "#98A2B3",
}
STATUS_DARK = {
    "active":   "#027A48",
    "planned":  "#175CD3",
    "inactive": "#B42318",
    "unknown":  "#667085",
}

# Premium hall color palette — each hall gets a unique tint (Apple/Google style)
HALL_PALETTE = [
    {"fill": "#EFF6FF", "border": "#93C5FD", "header": "#DBEAFE", "label": "#1D4ED8"},  # Blue
    {"fill": "#F0FDF4", "border": "#86EFAC", "header": "#DCFCE7", "label": "#15803D"},  # Green
    {"fill": "#FDF4FF", "border": "#D8B4FE", "header": "#F3E8FF", "label": "#7E22CE"},  # Purple
    {"fill": "#FFFBEB", "border": "#FCD34D", "header": "#FEF3C7", "label": "#B45309"},  # Amber
    {"fill": "#FFF1F2", "border": "#FDA4AF", "header": "#FFE4E6", "label": "#BE123C"},  # Rose
    {"fill": "#F0FDFA", "border": "#5EEAD4", "header": "#CCFBF1", "label": "#0F766E"},  # Teal
]


# ── Helper functions ──────────────────────────────────────────────────────────

def _parse_row_col(identifier: str) -> tuple[int, int]:
    """
    Parse facility IDs like 'A1', 'B2', 'A-01', 'RACK-B3' into (row, col).
    Falls back to (0, i) if no letter prefix found.
    """
    s = identifier.upper().strip()
    row, col = 0, 0
    for i, ch in enumerate(s):
        if ch.isalpha():
            row = ord(ch) - ord("A")
        elif ch.isdigit():
            num_str = ""
            j = i
            while j < len(s) and s[j].isdigit():
                num_str += s[j]
                j += 1
            try:
                col = int(num_str) - 1
            except ValueError:
                col = 0
            break
    return row, col


def _hall_dimensions(hall_racks: list[dict]) -> dict:
    """Calculate grid dimensions for a hall based on its racks."""
    if not hall_racks:
        return {"cols": 1, "rows": 1, "width": 0, "height": 0}

    max_col = 0
    max_row = 0
    for rack in hall_racks:
        r, c = _parse_row_col(rack.get("name", rack.get("serial", "A1")))
        max_row = max(max_row, r)
        max_col = max(max_col, c)

    cols = max_col + 1
    rows = max_row + 1

    # Two rows per aisle (front + back), separated by AISLE_H gap
    aisles = max(1, (rows + 1) // 2)
    zone_w = ZONE_PAD_X * 2 + cols * RACK_W + (cols - 1) * GAP_X
    zone_h = (
        ZONE_PAD_TOP
        + ZONE_LABEL_H
        + aisles * (2 * RACK_H + AISLE_H + GAP_Y)
        + ZONE_PAD_BOT
    )
    return {"cols": cols, "rows": rows, "width": zone_w, "height": zone_h}


def _draw_rack(
    fig: go.Figure,
    rx: float,
    ry: float,
    status: str,
    name: str,
    rack_data: dict,
    dc_id: str,
) -> None:
    """Draw a single rack: shadow, body, gloss strip, LED, hover trace."""
    fill = STATUS_FILL.get(status, STATUS_FILL["unknown"])
    dark = STATUS_DARK.get(status, STATUS_DARK["unknown"])

    # Shadow
    fig.add_shape(
        type="rect",
        x0=rx + 2, y0=ry - 2,
        x1=rx + RACK_W + 2, y1=ry + RACK_H - 2,
        fillcolor="rgba(0,0,0,0.12)",
        line_width=0,
        layer="below",
    )
    # Rack body
    fig.add_shape(
        type="rect",
        x0=rx, y0=ry,
        x1=rx + RACK_W, y1=ry + RACK_H,
        fillcolor=fill,
        line=dict(color=dark, width=1.2),
        layer="above",
    )
    # Gloss strip (top highlight)
    fig.add_shape(
        type="rect",
        x0=rx + 1, y0=ry + RACK_H - 5,
        x1=rx + RACK_W - 1, y1=ry + RACK_H - 1,
        fillcolor="rgba(255,255,255,0.28)",
        line_width=0,
        layer="above",
    )
    # LED dot
    fig.add_shape(
        type="circle",
        x0=rx + RACK_W - 6, y0=ry + 3,
        x1=rx + RACK_W - 3, y1=ry + 6,
        fillcolor="#FFFFFF" if status == "active" else "#FF4444",
        line_width=0,
        layer="above",
    )
    # Invisible hover trace
    u_height = rack_data.get("u_height", "?")
    energy = rack_data.get("kabin_enerji", "?")
    rack_type = rack_data.get("rack_type", "")
    hover_text = (
        f"<b>{name}</b><br>"
        f"Status: {status.title()}<br>"
        f"U Height: {u_height}U<br>"
        f"Power: {energy} kW<br>"
        f"Type: {rack_type}"
    )
    fig.add_trace(
        go.Scatter(
            x=[(rx + rx + RACK_W) / 2],
            y=[(ry + ry + RACK_H) / 2],
            mode="markers",
            marker=dict(size=max(RACK_W, RACK_H) * 1.5, opacity=0, color=fill),
            hovertemplate=hover_text + "<extra></extra>",
            customdata=[[dc_id, name, status, u_height, energy, rack_type]],
            showlegend=False,
            name=name,
        )
    )


def _draw_hall_zone(
    fig: go.Figure,
    hx: float,
    hy: float,
    hall_name: str,
    hall_racks: list[dict],
    dims: dict,
    dc_id: str,
    color: dict | None = None,
) -> None:
    """Draw one hall zone: background rect, colored header band, label, racks, aisle gaps."""
    zone_w = dims["width"]
    zone_h = dims["height"]
    hc = color or HALL_PALETTE[0]

    # Drop shadow (behind the hall card)
    fig.add_shape(
        type="rect",
        x0=hx + 3, y0=hy - 3,
        x1=hx + zone_w + 3, y1=hy + zone_h - 3,
        fillcolor="rgba(0,0,0,0.07)",
        line_width=0,
        layer="below",
    )
    # Zone body
    fig.add_shape(
        type="rect",
        x0=hx, y0=hy,
        x1=hx + zone_w, y1=hy + zone_h,
        fillcolor=hc["fill"],
        line=dict(color=hc["border"], width=1.5),
        layer="below",
    )
    # Colored header band at top
    fig.add_shape(
        type="rect",
        x0=hx, y0=hy + zone_h - ZONE_LABEL_H - ZONE_PAD_TOP,
        x1=hx + zone_w, y1=hy + zone_h,
        fillcolor=hc["header"],
        line=dict(color=hc["border"], width=0),
        layer="below",
    )
    # Left accent stripe
    fig.add_shape(
        type="rect",
        x0=hx, y0=hy,
        x1=hx + 4, y1=hy + zone_h,
        fillcolor=hc["border"],
        line_width=0,
        layer="below",
    )
    # Hall label annotation
    fig.add_annotation(
        x=hx + zone_w / 2,
        y=hy + zone_h - ZONE_PAD_TOP / 2 - ZONE_LABEL_H / 2,
        text=f"<b>{hall_name}</b>",
        showarrow=False,
        font=dict(size=11, color=hc["label"], family="DM Sans, sans-serif"),
        xanchor="center",
        yanchor="middle",
    )

    # Build grid positions
    rack_positions: dict[tuple[int, int], dict] = {}
    for rack in hall_racks:
        r, c = _parse_row_col(rack.get("name", rack.get("serial", "A1")))
        rack_positions[(r, c)] = rack

    cols = dims["cols"]
    rows = dims["rows"]

    for row_idx in range(rows):
        aisle_group = row_idx // 2
        within_aisle = row_idx % 2  # 0 = front row, 1 = back row

        row_y = (
            hy
            + ZONE_PAD_BOT
            + aisle_group * (2 * RACK_H + AISLE_H + GAP_Y)
            + within_aisle * (RACK_H + GAP_Y)
        )

        for col_idx in range(cols):
            col_x = hx + ZONE_PAD_X + col_idx * (RACK_W + GAP_X)
            rack = rack_positions.get((row_idx, col_idx))
            if rack:
                status = (rack.get("status") or "unknown").lower()
                name = rack.get("name", f"R{row_idx+1}-C{col_idx+1}")
                _draw_rack(fig, col_x, row_y, status, name, rack, dc_id)
            else:
                # Empty slot — transparent with subtle dashed border matching hall color
                slot_border = hc.get("border", "#D1D5DB") if color else "#D1D5DB"
                fig.add_shape(
                    type="rect",
                    x0=col_x, y0=row_y,
                    x1=col_x + RACK_W, y1=row_y + RACK_H,
                    fillcolor="rgba(255,255,255,0.4)",
                    line=dict(color=slot_border, width=0.8, dash="dot"),
                    layer="above",
                )

        # Aisle label
        if within_aisle == 0 and row_idx + 1 < rows:
            aisle_y = row_y + RACK_H + GAP_Y / 2
            aisle_label_x = hx + ZONE_PAD_X + (cols * (RACK_W + GAP_X) - GAP_X) / 2
            aisle_color = hc.get("label", "#98A2B3") if color else "#98A2B3"
            fig.add_annotation(
                x=aisle_label_x,
                y=aisle_y,
                text=f"── Aisle {aisle_group + 1} ──",
                showarrow=False,
                font=dict(size=8, color=aisle_color, family="DM Sans, sans-serif"),
                xanchor="center",
                yanchor="middle",
            )


# ── Figure builder ────────────────────────────────────────────────────────────

def build_floor_map_figure(racks: list[dict], dc_id: str) -> go.Figure:
    """Main floor plan figure: groups racks by hall, renders zones in a grid."""
    fig = go.Figure()

    # Group racks by hall
    halls: dict[str, list[dict]] = {}
    for rack in racks:
        hall = rack.get("hall_name") or "Main Hall"
        halls.setdefault(hall, []).append(rack)

    if not halls:
        halls["Main Hall"] = []

    hall_names = sorted(halls.keys())
    hall_dims = {h: _hall_dimensions(halls[h]) for h in hall_names}

    # Arrange halls in a 2-column grid
    cursor_x = FLOOR_PAD
    cursor_y = FLOOR_PAD
    col_widths = [0.0, 0.0]
    row_height = 0.0
    total_w = FLOOR_PAD
    total_h = FLOOR_PAD

    hall_positions: dict[str, tuple[float, float]] = {}

    for i, hall_name in enumerate(hall_names):
        col = i % HALLS_PER_ROW
        row = i // HALLS_PER_ROW

        if col == 0 and row > 0:
            cursor_y += row_height + HALL_ROW_GAP
            cursor_x = FLOOR_PAD
            row_height = 0.0
            col_widths = [0.0, 0.0]

        d = hall_dims[hall_name]
        hall_positions[hall_name] = (cursor_x + col * (col_widths[0] + HALL_COL_GAP) if col == 1 else cursor_x, cursor_y)
        col_widths[col] = d["width"]
        row_height = max(row_height, d["height"])

    # Recompute positions properly
    hall_positions = {}
    col = 0
    row = 0
    x_offsets = [FLOOR_PAD, FLOOR_PAD]
    y_offset = FLOOR_PAD
    row_h = 0.0
    prev_col_width = 0.0

    for i, hall_name in enumerate(hall_names):
        col = i % HALLS_PER_ROW
        if col == 0 and i > 0:
            y_offset += row_h + HALL_ROW_GAP
            row_h = 0.0
            x_offsets = [FLOOR_PAD, FLOOR_PAD]
            prev_col_width = 0.0

        d = hall_dims[hall_name]
        if col == 0:
            hx = FLOOR_PAD
            prev_col_width = d["width"]
        else:
            hx = FLOOR_PAD + prev_col_width + HALL_COL_GAP

        hy = y_offset
        hall_positions[hall_name] = (hx, hy)
        row_h = max(row_h, d["height"])
        total_w = max(total_w, hx + d["width"] + FLOOR_PAD)
        total_h = max(total_h, hy + d["height"] + FLOOR_PAD)

    # Draw building perimeter first (below everything)
    wall_pad = FLOOR_PAD / 2
    # Outer shadow
    fig.add_shape(
        type="rect",
        x0=wall_pad + 4, y0=wall_pad - 4,
        x1=total_w - wall_pad + 4, y1=total_h - wall_pad - 4,
        fillcolor="rgba(0,0,0,0.08)",
        line_width=0,
        layer="below",
    )
    # Building interior floor (slightly warmer than outer bg)
    fig.add_shape(
        type="rect",
        x0=wall_pad, y0=wall_pad,
        x1=total_w - wall_pad, y1=total_h - wall_pad,
        fillcolor="#F8FAFC",
        line=dict(color="#CBD5E1", width=2),
        layer="below",
    )

    # Draw hall zones — each with its own color from the palette
    for i, hall_name in enumerate(hall_names):
        hx, hy = hall_positions[hall_name]
        palette_color = HALL_PALETTE[i % len(HALL_PALETTE)]
        _draw_hall_zone(fig, hx, hy, hall_name, halls[hall_name], hall_dims[hall_name], dc_id, color=palette_color)

    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="#E2E8F0",
        plot_bgcolor="#E2E8F0",
        xaxis=dict(
            range=[-FLOOR_PAD / 2, total_w],
            showgrid=False, zeroline=False, visible=False,
            fixedrange=False,
        ),
        yaxis=dict(
            range=[-FLOOR_PAD / 2, total_h],
            showgrid=False, zeroline=False, visible=False,
            fixedrange=False,
            scaleanchor="x",
            scaleratio=1,
        ),
        height=600,
        dragmode="pan",
        hoverlabel=dict(
            bgcolor="rgba(255,255,255,0.97)",
            bordercolor="#E4E7EC",
            font=dict(size=12, color="#344054"),
        ),
        newshape=dict(line_color="#4318FF"),
    )

    return fig


# ── Layout builder ────────────────────────────────────────────────────────────

def build_floor_map_layout(dc_id: str, dc_name: str, racks: list[dict]) -> html.Div:
    """Full floor map page layout with header, Plotly canvas, legend, detail panel."""

    # Count rack statuses for header badges
    status_counts: dict[str, int] = {}
    halls_set: set[str] = set()
    for rack in racks:
        s = (rack.get("status") or "unknown").lower()
        status_counts[s] = status_counts.get(s, 0) + 1
        halls_set.add(rack.get("hall_name") or "Main Hall")

    total_racks = len(racks)

    # Status badges
    status_badges = []
    badge_cfg = [
        ("active",   "teal",  "Active"),
        ("inactive", "red",   "Inactive"),
        ("planned",  "blue",  "Planned"),
        ("unknown",  "gray",  "Unknown"),
    ]
    for key, color, label in badge_cfg:
        cnt = status_counts.get(key, 0)
        if cnt:
            status_badges.append(
                dmc.Badge(f"{cnt} {label}", color=color, variant="light", size="sm", radius="sm")
            )

    # Hall badges
    hall_badges = [
        dmc.Badge(h, color="indigo", variant="dot", size="sm", radius="sm")
        for h in sorted(halls_set)
    ]

    fig = build_floor_map_figure(racks, dc_id)

    # Legend rows
    legend_items = [
        ("fm-swatch-active",   "Active"),
        ("fm-swatch-inactive", "Inactive"),
        ("fm-swatch-planned",  "Planned"),
        ("fm-swatch-unknown",  "Unknown"),
    ]
    legend_children = []
    for cls, lbl in legend_items:
        legend_children.append(
            dmc.Group(
                gap="xs",
                children=[
                    html.Div(className=f"fm-legend-swatch {cls}"),
                    dmc.Text(lbl, size="xs", c="#667085"),
                ],
            )
        )

    detail_placeholder = html.Div(
        className="floor-map-detail-empty",
        children=[
            html.Div(
                className="fm-empty-icon-wrap",
                children=[DashIconify(icon="solar:server-square-bold-duotone", width=28, color="#A3AED0")],
            ),
            dmc.Text("Click a rack to inspect", size="sm", c="#A3AED0", mt="md"),
            dmc.Text("Select any rack on the floor plan to see its unit details.", size="xs", c="#D0D5DD", ta="center", maw=200),
        ],
    )

    return html.Div(
        className="floor-map-page",
        children=[
            # ── Header ──────────────────────────────────────────────────────
            html.Div(
                className="floor-map-header",
                children=[
                    dmc.Group(
                        gap="md",
                        children=[
                            dmc.Button(
                                id="back-to-global-btn",
                                children=[
                                    DashIconify(icon="solar:arrow-left-bold", width=16),
                                    html.Span(" Back", style={"marginLeft": "4px"}),
                                ],
                                variant="subtle",
                                color="gray",
                                size="sm",
                                radius="md",
                                style={"fontWeight": 600},
                            ),
                            dmc.Divider(orientation="vertical", style={"height": "24px"}),
                            dmc.ThemeIcon(
                                DashIconify(icon="solar:buildings-bold-duotone", width=18),
                                size="lg",
                                radius="md",
                                color="indigo",
                                variant="light",
                            ),
                            html.Div([
                                dmc.Text(dc_name or dc_id, fw=700, size="lg", c="#1B2559"),
                                dmc.Text(f"{total_racks} racks · {len(halls_set)} hall(s)", size="xs", c="#A3AED0"),
                            ]),
                        ],
                    ),
                    dmc.Group(
                        gap="xs",
                        children=status_badges + hall_badges,
                    ),
                ],
            ),

            # ── Main grid (8 / 4) ────────────────────────────────────────────
            dmc.Grid(
                gutter="md",
                mt="sm",
                children=[
                    # Left: floor plan canvas + legend
                    dmc.GridCol(
                        span=8,
                        children=[
                            dmc.Paper(
                                radius="lg",
                                className="floor-map-canvas-wrap",
                                children=[
                                    dcc.Graph(
                                        id="floor-map-graph",
                                        figure=fig,
                                        config={
                                            "displayModeBar": True,
                                            "modeBarButtonsToRemove": [
                                                "select2d",
                                                "lasso2d",
                                                "autoScale2d",
                                                "toggleSpikelines",
                                            ],
                                            "displaylogo": False,
                                            "scrollZoom": True,
                                        },
                                        style={"height": "600px", "borderRadius": "12px"},
                                    ),
                                ],
                            ),
                            # Legend
                            dmc.Group(
                                gap="lg",
                                mt="xs",
                                px="xs",
                                children=legend_children,
                            ),
                        ],
                    ),
                    # Right: rack detail panel
                    dmc.GridCol(
                        span=4,
                        children=[
                            dmc.Paper(
                                id="floor-map-rack-detail",
                                radius="lg",
                                p="md",
                                className="floor-map-detail-panel",
                                children=[detail_placeholder],
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )
