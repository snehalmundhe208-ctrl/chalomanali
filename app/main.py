"""
Main Router Script for Commodity Derivatives Intelligence.
Configures st.navigation with explicit unique url_path parameters.
"""

import streamlit as st
import sys
import os

# Ensure project root is on sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from assets.theme import init_page_theme
from app.pages import (
    p1_overview,
    p2_contract_explorer,
    p3_relative_value,
    p4_term_structure,
    p5_backtest_lab,
    p6_contract_lifecycle,
    p7_data_quality,
    p8_admin,
    p9_methodology,
)

st.set_page_config(
    page_title="Commodity Derivatives Intelligence | Team 404_Altitude",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply global styling
init_page_theme()

# Sidebar Logo / Title Block
st.sidebar.markdown(
    """
    <div style="padding: 10px 0 15px 0; border-bottom: 1px solid #2A3E5C; margin-bottom: 15px;">
        <h2 style="color: #E8A317; font-family: 'Poppins', sans-serif; font-weight: 800; margin: 0; font-size: 1.35rem;">
            📈 Team 404_Altitude
        </h2>
        <p style="color: #94A3B8; font-size: 0.8rem; margin: 2px 0 0 0; font-weight: 500;">
            Commodity Derivatives Intelligence
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# Register pages with explicit unique url_path parameters
page1 = st.Page(p1_overview.render, title="Overview", icon=":material/dashboard:", url_path="overview", default=True)
page2 = st.Page(p2_contract_explorer.render, title="Contract Explorer", icon=":material/analytics:", url_path="contract-explorer")
page3 = st.Page(p3_relative_value.render, title="Relative Value", icon=":material/compare_arrows:", url_path="relative-value")
page4 = st.Page(p4_term_structure.render, title="Term Structure", icon=":material/show_chart:", url_path="term-structure")
page5 = st.Page(p5_backtest_lab.render, title="Backtest Lab", icon=":material/science:", url_path="backtest-lab")
page6 = st.Page(p6_contract_lifecycle.render, title="Lifecycle", icon=":material/event:", url_path="lifecycle")
page7 = st.Page(p7_data_quality.render, title="Data Quality", icon=":material/verified:", url_path="data-quality")
page8 = st.Page(p8_admin.render, title="Admin", icon=":material/admin_panel_settings:", url_path="admin")
page9 = st.Page(p9_methodology.render, title="Methodology", icon=":material/menu_book:", url_path="methodology")

pg = st.navigation({
    "Core Dashboard": [page1, page2, page3],
    "Analytics & Lab": [page4, page5, page6],
    "System & Quality": [page7, page8, page9]
})

pg.run()
