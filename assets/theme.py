"""
Shared UI Theme Helper for Commodity Derivatives Intelligence.
Injects custom CSS on every page and renders standard headers & hero banners.
"""

import streamlit as st
import os
from assets.plotly_theme import apply_custom_plotly_theme

def init_page_theme():
    """
    Applies custom CSS and Plotly theme to the current Streamlit page.
    Must be called at the top of every page render() function.
    """
    # Apply Plotly template
    apply_custom_plotly_theme()
    
    # Inject assets/style.css
    css_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "style.css"))
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def render_hero_banner(title: str, subtitle: str, is_synthetic: bool = False):
    """
    Renders standardized hero header banner with LIVE / DEMO DATA status badge.
    """
    badge_html = '<span class="status-pill-demo">DATA SOURCE: DEMO DATA (synthetic)</span>' if is_synthetic else '<span class="status-pill-live">DATA SOURCE: LIVE (MCX Bhavcopy)</span>'
    
    st.markdown(
        f"""
        <div class="hero-banner">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <h1 class="hero-title">{title}</h1>
                    <p class="hero-subtitle">{subtitle}</p>
                </div>
                <div>{badge_html}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
