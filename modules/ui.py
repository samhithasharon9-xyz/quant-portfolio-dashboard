"""
Visual identity for the dashboard: colour palette, global CSS, the logo
header, and shared chart helpers so every chart looks consistent.

Keeping this separate from main.py means design changes never touch
the analytics code.
"""
import streamlit as st
import plotly.graph_objects as go

# ---------------- Palette ----------------
ESPRESSO = "#322D29"
BURGUNDY = "#72383D"
TAUPE = "#AC9C8D"
SAND = "#D1C7BD"
MIST = "#D9D9D9"
CREAM = "#EFE9E1"

# Moss green: used sparingly as an accent only
MOSS_DARK = "#484E39"
MOSS = "#5F6749"
MOSS_TINT = "#8C9472"      # lighter moss, only where it must stay visible on dark

BURGUNDY_TINT = "#A0525A"  # lighter burgundy, for lines on the dark background
NEON = "#4ade80"           # signature colour for key numbers
PAGE_BG = "#221E1B"        # must match backgroundColor in .streamlit/config.toml
GRID = "rgba(172, 156, 141, 0.14)"

SERIES_COLORS = [SAND, BURGUNDY_TINT, TAUPE, CREAM, MIST, MOSS_TINT]

# Correlation scale: moss (-1) -> espresso (0) -> burgundy (+1)
CORR_SCALE = [
    [0.0, MOSS_TINT],
    [0.25, MOSS_DARK],
    [0.5, ESPRESSO],
    [0.75, BURGUNDY],
    [1.0, BURGUNDY_TINT],
]

# Static charts (bars, heatmap): no zoom, no toolbar
STATIC_CONFIG = {"scrollZoom": False, "doubleClick": False, "displayModeBar": False}

# Zoomable charts: scrolling still scrolls the page; zoom only via the +/- buttons
ZOOM_CONFIG = {
    "scrollZoom": False,
    "doubleClick": False,
    "displayModeBar": True,
    "displaylogo": False,
    "modeBarButtons": [["zoomIn2d", "zoomOut2d", "resetScale2d"]],
}


# ---------------- Logo ----------------
def _frontier_logo(bg_top, bg_bottom, border, uid):
    """Efficient frontier curve, the optimal portfolio (neon), and weaker portfolios below it."""
    return (
        f'<svg width="56" height="56" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg" style="flex-shrink:0">'
        f'<defs><linearGradient id="{uid}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{bg_top}"/><stop offset="1" stop-color="{bg_bottom}"/></linearGradient></defs>'
        f'<rect x="2" y="2" width="60" height="60" rx="15" fill="url(#{uid})"/>'
        f'<rect x="2.5" y="2.5" width="59" height="59" rx="14.5" fill="none" stroke="{border}" stroke-opacity="0.35"/>'
        '<path d="M15 50 L15 14 M15 50 L51 50" stroke="#EFE9E1" stroke-opacity="0.22" stroke-width="1.2" fill="none"/>'
        '<g fill="#D1C7BD" fill-opacity="0.75">'
        '<circle cx="31" cy="39" r="1.9"/><circle cx="38" cy="34" r="1.9"/><circle cx="44" cy="41" r="1.9"/>'
        '<circle cx="35" cy="45" r="1.9"/><circle cx="46" cy="29" r="1.9"/><circle cx="26" cy="44" r="1.9"/>'
        '<circle cx="41" cy="24.5" r="1.7"/></g>'
        '<path d="M18 46 C20 30 31 20 51 16" stroke="#EFE9E1" stroke-width="3" fill="none" stroke-linecap="round"/>'
        '<circle cx="25.4" cy="28.6" r="4.6" fill="#4ade80" stroke="#EFE9E1" stroke-width="1.6"/>'
        '</svg>'
    )


_DIE_ISO_LOGO = (
    '<svg width="56" height="56" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg" style="flex-shrink:0"><path d="M32 4 L58 18 L32 32 L6 18 Z" fill="#8F4C53"/><path d="M6 18 L32 32 L32 60 L6 46 Z" fill="#72383D"/><path d="M58 18 L32 32 L32 60 L58 46 Z" fill="#522429"/><path d="M32 32 L32 60 M32 32 L6 18 M32 32 L58 18" stroke="#EFE9E1" stroke-opacity="0.22" stroke-width="1"/><path d="M32 4 L58 18 L58 46 L32 60 L6 46 L6 18 Z" fill="none" stroke="#EFE9E1" stroke-opacity="0.4" stroke-width="1.3" stroke-linejoin="round"/><g transform="matrix(26 -14 26 14 6 18)" fill="#0E0C0B"><circle cx="0.25" cy="0.25" r="0.088"/><circle cx="0.75" cy="0.25" r="0.088"/><circle cx="0.5" cy="0.5" r="0.088"/><circle cx="0.25" cy="0.75" r="0.088"/><circle cx="0.75" cy="0.75" r="0.088"/></g><g transform="matrix(26 14 0 28 6 18)" fill="#0E0C0B"><circle cx="0.24" cy="0.24" r="0.092"/><circle cx="0.5" cy="0.5" r="0.092"/><circle cx="0.76" cy="0.76" r="0.092"/></g><g transform="matrix(26 -14 0 28 32 32)" fill="#0E0C0B"><circle cx="0.27" cy="0.27" r="0.092"/><circle cx="0.73" cy="0.27" r="0.092"/><circle cx="0.27" cy="0.73" r="0.092"/><circle cx="0.73" cy="0.73" r="0.092"/></g></svg>'
)

_DIE_FLAT_LOGO = (
    '<svg width="56" height="56" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg" style="flex-shrink:0"><defs><linearGradient id="qf-body" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#8A4A51"/><stop offset="1" stop-color="#5A2A30"/></linearGradient></defs><rect x="3" y="3" width="58" height="58" rx="14" fill="url(#qf-body)"/><rect x="3.6" y="3.6" width="56.8" height="56.8" rx="13.4" fill="none" stroke="#EFE9E1" stroke-opacity="0.3" stroke-width="1.2"/><circle cx="20" cy="20" r="5.4" fill="#0E0C0B" stroke="#EFE9E1" stroke-opacity="0.14" stroke-width="0.8"/><circle cx="44" cy="20" r="5.4" fill="#0E0C0B" stroke="#EFE9E1" stroke-opacity="0.14" stroke-width="0.8"/><circle cx="32" cy="32" r="5.4" fill="#0E0C0B" stroke="#EFE9E1" stroke-opacity="0.14" stroke-width="0.8"/><circle cx="20" cy="44" r="5.4" fill="#0E0C0B" stroke="#EFE9E1" stroke-opacity="0.14" stroke-width="0.8"/><circle cx="44" cy="44" r="5.4" fill="#0E0C0B" stroke="#EFE9E1" stroke-opacity="0.14" stroke-width="0.8"/></svg>'
)

_DIE_ISO_BRIGHT_LOGO = (
    '<svg width="56" height="56" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg" style="flex-shrink:0"><path d="M32 4 L58 18 L32 32 L6 18 Z" fill="#B85A64"/><path d="M6 18 L32 32 L32 60 L6 46 Z" fill="#9A4650"/><path d="M58 18 L32 32 L32 60 L58 46 Z" fill="#702F38"/><path d="M32 32 L32 60 M32 32 L6 18 M32 32 L58 18" stroke="#EFE9E1" stroke-opacity="0.24" stroke-width="1"/><path d="M32 4 L58 18 L58 46 L32 60 L6 46 L6 18 Z" fill="none" stroke="#EFE9E1" stroke-opacity="0.42" stroke-width="1.3" stroke-linejoin="round"/><g transform="matrix(26 -14 26 14 6 18)" fill="#0E0C0B"><circle cx="0.25" cy="0.25" r="0.088"/><circle cx="0.75" cy="0.25" r="0.088"/><circle cx="0.5" cy="0.5" r="0.088"/><circle cx="0.25" cy="0.75" r="0.088"/><circle cx="0.75" cy="0.75" r="0.088"/></g><g transform="matrix(26 14 0 28 6 18)" fill="#0E0C0B"><circle cx="0.24" cy="0.24" r="0.092"/><circle cx="0.5" cy="0.5" r="0.092"/><circle cx="0.76" cy="0.76" r="0.092"/></g><g transform="matrix(26 -14 0 28 32 32)" fill="#0E0C0B"><circle cx="0.27" cy="0.27" r="0.092"/><circle cx="0.73" cy="0.27" r="0.092"/><circle cx="0.27" cy="0.73" r="0.092"/><circle cx="0.73" cy="0.73" r="0.092"/></g></svg>'
)

_DIE_ISO_GLOSSY_LOGO = (
    '<svg width="56" height="56" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg" style="flex-shrink:0"><defs><linearGradient id="gl-top" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#8A3340"/><stop offset="1" stop-color="#5E212B"/></linearGradient><linearGradient id="gl-left" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#651F2B"/><stop offset="1" stop-color="#430F18"/></linearGradient><linearGradient id="gl-right" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#4A121C"/><stop offset="1" stop-color="#2A0910"/></linearGradient><linearGradient id="gl-shine" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#FFFFFF" stop-opacity="0.62"/><stop offset="0.55" stop-color="#FFFFFF" stop-opacity="0.12"/><stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/></linearGradient><linearGradient id="gl-shine2" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFFFFF" stop-opacity="0.34"/><stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/></linearGradient><radialGradient id="gl-pip" cx="0.34" cy="0.3" r="0.8"><stop offset="0" stop-color="#4A4644"/><stop offset="0.45" stop-color="#0E0C0B"/><stop offset="1" stop-color="#000000"/></radialGradient><clipPath id="gl-clip-top"><path d="M32 4 L58 18 L32 32 L6 18 Z"/></clipPath><clipPath id="gl-clip-left"><path d="M6 18 L32 32 L32 60 L6 46 Z"/></clipPath></defs><path d="M32 4 L58 18 L32 32 L6 18 Z" fill="url(#gl-top)"/><path d="M6 18 L32 32 L32 60 L6 46 Z" fill="url(#gl-left)"/><path d="M58 18 L32 32 L32 60 L58 46 Z" fill="url(#gl-right)"/><g clip-path="url(#gl-clip-top)"><ellipse cx="25" cy="11.5" rx="17" ry="6.2" transform="rotate(27 25 11.5)" fill="url(#gl-shine)"/></g><g clip-path="url(#gl-clip-left)"><path d="M8.5 21 L12.5 23.2 L12.5 41.5 L8.5 39.3 Z" fill="url(#gl-shine2)"/></g><path d="M32 32 L32 60 M32 32 L6 18 M32 32 L58 18" stroke="#EFE9E1" stroke-opacity="0.18" stroke-width="1"/><path d="M32 4 L58 18 L58 46 L32 60 L6 46 L6 18 Z" fill="none" stroke="#EFE9E1" stroke-opacity="0.38" stroke-width="1.3" stroke-linejoin="round"/><path d="M6.8 17.6 L32 4.2 L57.2 17.6" fill="none" stroke="#FFFFFF" stroke-opacity="0.7" stroke-width="1.1" stroke-linecap="round" stroke-linejoin="round"/><g transform="matrix(26 -14 26 14 6 18)" fill="url(#gl-pip)"><circle cx="0.25" cy="0.25" r="0.088"/><circle cx="0.75" cy="0.25" r="0.088"/><circle cx="0.5" cy="0.5" r="0.088"/><circle cx="0.25" cy="0.75" r="0.088"/><circle cx="0.75" cy="0.75" r="0.088"/></g><g transform="matrix(26 14 0 28 6 18)" fill="url(#gl-pip)"><circle cx="0.24" cy="0.24" r="0.092"/><circle cx="0.5" cy="0.5" r="0.092"/><circle cx="0.76" cy="0.76" r="0.092"/></g><g transform="matrix(26 -14 0 28 32 32)" fill="url(#gl-pip)"><circle cx="0.27" cy="0.27" r="0.092"/><circle cx="0.73" cy="0.27" r="0.092"/><circle cx="0.27" cy="0.73" r="0.092"/><circle cx="0.73" cy="0.73" r="0.092"/></g></svg>'
)

_DIE_ISO_MATTE_LOGO = (
    '<svg width="56" height="56" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg" style="flex-shrink:0"><path d="M32 4 L58 18 L32 32 L6 18 Z" fill="#74272F"/><path d="M6 18 L32 32 L32 60 L6 46 Z" fill="#561A23"/><path d="M58 18 L32 32 L32 60 L58 46 Z" fill="#3A0F16"/><path d="M32 32 L32 60 M32 32 L6 18 M32 32 L58 18" stroke="#EFE9E1" stroke-opacity="0.2" stroke-width="1"/><path d="M32 4 L58 18 L58 46 L32 60 L6 46 L6 18 Z" fill="none" stroke="#EFE9E1" stroke-opacity="0.36" stroke-width="1.3" stroke-linejoin="round"/><g transform="matrix(26 -14 26 14 6 18)" fill="#0A0808"><circle cx="0.25" cy="0.25" r="0.088"/><circle cx="0.75" cy="0.25" r="0.088"/><circle cx="0.5" cy="0.5" r="0.088"/><circle cx="0.25" cy="0.75" r="0.088"/><circle cx="0.75" cy="0.75" r="0.088"/></g><g transform="matrix(26 14 0 28 6 18)" fill="#0A0808"><circle cx="0.24" cy="0.24" r="0.092"/><circle cx="0.5" cy="0.5" r="0.092"/><circle cx="0.76" cy="0.76" r="0.092"/></g><g transform="matrix(26 -14 0 28 32 32)" fill="#0A0808"><circle cx="0.27" cy="0.27" r="0.092"/><circle cx="0.73" cy="0.27" r="0.092"/><circle cx="0.27" cy="0.73" r="0.092"/><circle cx="0.73" cy="0.73" r="0.092"/></g></svg>'
)

LOGOS = {
    "1": _frontier_logo("#484E39", "#5F6749", "#D1C7BD", "qpi-moss"),   # frontier on moss
    "2": _frontier_logo("#3A342F", "#2A2521", "#AC9C8D", "qpi-esp"),    # frontier on espresso
    "3": _DIE_ISO_LOGO,                                                 # 3D burgundy die, black pips
    "4": _DIE_FLAT_LOGO,                                                # flat burgundy die, black pips
    "5": _DIE_ISO_BRIGHT_LOGO,                                          # 3D die, brighter burgundy
    "6": _DIE_ISO_GLOSSY_LOGO,                                          # 3D die, deep burgundy, glossy
    "7": _DIE_ISO_MATTE_LOGO,                                           # 3D die, deep burgundy, matte
}
LOGO_CHOICE = "7"   # change to "1", "2", "4", "5", "6" or "7" to switch logo (favicon follows automatically)

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=EB+Garamond:wght@500;600;700&family=IBM+Plex+Mono:wght@500;600&display=swap');

/* Top bar blends into the page */
[data-testid="stHeader"] { background: transparent; }

/* Headings: bookish serif, like the textbook covers in the moodboard */
h1, h2, h3, h4 {
    font-family: 'EB Garamond', Georgia, serif !important;
    color: #EFE9E1 !important;
    font-weight: 600 !important;
    letter-spacing: 0.2px;
}
h3 { font-size: 1.75rem !important; }
h4 { font-size: 1.3rem !important; }
[data-testid="stHeaderActionElements"] { display: none; }

/* App header */
.qpi-header { display: flex; align-items: center; gap: 18px; margin: 0.2rem 0 0.4rem 0; }
.qpi-title {
    font-family: 'EB Garamond', Georgia, serif;
    font-size: 2.7rem; font-weight: 600; line-height: 1.05;
    color: #EFE9E1;
}
.qpi-subtitle { color: #AC9C8D; font-size: 1.02rem; margin-top: 4px; }

/* Metrics: ledger-style left rule, neon monospace figures */
[data-testid="stMetric"] {
    border-left: 2px solid #A0525A;
    padding: 4px 0 4px 14px;
}
[data-testid="stMetricLabel"], [data-testid="stMetricLabel"] p {
    color: #AC9C8D !important;
    font-size: 0.88rem !important;
}
[data-testid="stMetricValue"], [data-testid="stMetricValue"] div {
    font-family: 'IBM Plex Mono', monospace !important;
    color: #4ade80 !important;
    font-size: 1.55rem !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] { gap: 4px; }
.stTabs [data-baseweb="tab"] { padding: 10px 14px; }
.stTabs [data-baseweb="tab"] p { color: #AC9C8D; font-size: 0.98rem; }
.stTabs [aria-selected="true"] p { color: #EFE9E1 !important; }
.stTabs [data-baseweb="tab-highlight"] { background-color: #A0525A !important; }
.stTabs [data-baseweb="tab-border"] { background-color: rgba(172, 156, 141, 0.18); }

/* Captions */
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p { color: #AC9C8D !important; }

/* Sidebar */
[data-testid="stSidebar"] { border-right: 1px solid rgba(172, 156, 141, 0.15); }

/* Ticker chips: burgundy pills */
[data-baseweb="tag"] { background-color: #72383D !important; border-radius: 999px !important; }
[data-baseweb="tag"] span { color: #EFE9E1 !important; }

/* Zoom buttons: bottom-right corner of the chart */
.js-plotly-plot .plotly .modebar-container { top: auto !important; bottom: 0 !important; }
.js-plotly-plot .plotly .modebar { top: auto !important; bottom: 4px !important; right: 6px !important; }
.js-plotly-plot .plotly .modebar-group { border-radius: 8px; padding: 2px 4px !important; }

hr { border-color: rgba(172, 156, 141, 0.18) !important; }
.stButton > button[kind="primary"] { border-radius: 10px; font-weight: 600; }
</style>
"""


def apply_theme():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def render_header(title, subtitle):
    st.markdown(
        f'<div class="qpi-header">{LOGOS[LOGO_CHOICE]}<div>'
        f'<div class="qpi-title">{title}</div>'
        f'<div class="qpi-subtitle">{subtitle}</div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )


def style_fig(fig, height=420, x_title="", y_title="", show_legend=True):
    """Apply the dashboard's look to any Plotly figure (zoom locked by default)."""
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Source Sans Pro, sans-serif", color=SAND, size=13),
        margin=dict(l=8, r=8, t=36, b=8),
        hoverlabel=dict(bgcolor=ESPRESSO, bordercolor=TAUPE, font=dict(color=CREAM)),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
            bgcolor="rgba(0,0,0,0)", font=dict(color=SAND),
        ),
        modebar=dict(bgcolor="rgba(50, 45, 41, 0.92)", color=TAUPE, activecolor=CREAM),
        showlegend=show_legend,
        dragmode=False,
    )
    axis_style = dict(
        fixedrange=True, automargin=True, gridcolor=GRID, zeroline=False, linecolor=GRID,
        tickfont=dict(color=TAUPE), title_font=dict(color=TAUPE),
    )
    fig.update_xaxes(title_text=x_title, **axis_style)
    fig.update_yaxes(title_text=y_title, **axis_style)
    return fig


def show_chart(fig, key=None, zoomable=False):
    """Render a chart. zoomable=True adds +/- and reset buttons in the bottom-right corner."""
    if zoomable:
        fig.update_xaxes(fixedrange=False)
        fig.update_yaxes(fixedrange=False)
        fig.update_layout(margin=dict(b=46))  # room for the buttons under the axis
    st.plotly_chart(
        fig, width="stretch", theme=None, key=key,
        config=ZOOM_CONFIG if zoomable else STATIC_CONFIG,
    )


def weights_chart(weights, labels, color=SAND, height=None):
    """Horizontal bar chart of portfolio weights (or any 0-1 shares)."""
    values = [float(w) * 100 for w in weights]
    fig = go.Figure(go.Bar(
        x=values, y=list(labels), orientation="h",
        marker=dict(color=color, line=dict(width=0)),
        text=[f"{v:.1f}%" for v in values], textposition="outside",
        textfont=dict(color=CREAM, family="IBM Plex Mono, monospace", size=13),
        cliponaxis=False,
        hovertemplate="%{y}: %{x:.1f}%<extra></extra>",
    ))
    style_fig(fig, height=height or max(170, 48 * len(values) + 50), show_legend=False)
    fig.update_xaxes(range=[0, max(values) * 1.3 + 1], showgrid=False, showticklabels=False)
    fig.update_yaxes(showgrid=False, autorange="reversed")
    fig.update_layout(bargap=0.4, margin=dict(l=8, r=8, t=8, b=8))
    return fig