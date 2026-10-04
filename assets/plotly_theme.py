"""
Custom Plotly theme generator matching the pitch deck palette.
"""

import plotly.graph_objects as go
import plotly.io as pio

NAVY_BG = "#0F172A"
CARD_BG = "#1B2A41"
GOLD_ACCENT = "#E8A317"
TEXT_COLOR = "#F8FAFC"
MUTED_TEXT = "#94A3B8"
GRID_COLOR = "#334155"

def apply_custom_plotly_theme():
    """
    Registers and sets default Plotly theme template.
    """
    template = go.layout.Template()
    template.layout.paper_bgcolor = "rgba(0,0,0,0)"
    template.layout.plot_bgcolor = CARD_BG
    template.layout.font = dict(family="Inter, sans-serif", color=TEXT_COLOR, size=12)
    
    template.layout.xaxis = dict(
        gridcolor=GRID_COLOR,
        zerolinecolor=GRID_COLOR,
        showgrid=True,
        tickfont=dict(color=MUTED_TEXT),
        title_font=dict(color=TEXT_COLOR),
    )
    
    template.layout.yaxis = dict(
        gridcolor=GRID_COLOR,
        zerolinecolor=GRID_COLOR,
        showgrid=True,
        tickfont=dict(color=MUTED_TEXT),
        title_font=dict(color=TEXT_COLOR),
    )
    
    template.layout.legend = dict(
        font=dict(color=TEXT_COLOR),
        bgcolor="rgba(27, 42, 65, 0.8)",
        bordercolor=GRID_COLOR,
        borderwidth=1,
    )
    
    template.layout.colorway = [
        "#E8A317",  # Gold
        "#38BDF8",  # Cyan
        "#10B981",  # Emerald
        "#F43F5E",  # Rose
        "#A855F7",  # Purple
        "#F59E0B",  # Amber
    ]
    
    pio.templates["antigravity"] = template
    pio.templates.default = "antigravity"

def get_layout_defaults(title: str = "", x_title: str = "", y_title: str = "") -> dict:
    return dict(
        title=dict(text=title, font=dict(size=16, family="Poppins, sans-serif")),
        xaxis_title=x_title,
        yaxis_title=y_title,
        margin=dict(l=40, r=30, t=50, b=40),
        hovermode="x unified",
    )
