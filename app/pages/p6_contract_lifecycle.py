"""
Page 6: Contract Lifecycle & Expiry Schedule.
"""

import streamlit as st
import pandas as pd
import plotly.express as px

from assets.theme import init_page_theme, render_hero_banner
from data.loader import get_or_load_dataset
from core.config import CONTRACT_FACTS
from assets.plotly_theme import get_layout_defaults

def render():
    init_page_theme()
    df, _, is_synthetic = get_or_load_dataset()
    
    render_hero_banner(
        title="Contract Lifecycle & Expiry Schedules",
        subtitle="Visualizes contract listing, liquidity build-up, tender windows, and physical delivery expiry schedules",
        is_synthetic=is_synthetic
    )

    # 1. Lifecycle Rules Table
    with st.container(border=True):
        st.markdown("### MCX Contract Lifecycle Rules Matrix")
        lifecycle_rows = []
        for sym, facts in CONTRACT_FACTS.items():
            lifecycle_rows.append({
                "Contract": sym,
                "Expiry Window": facts["expiry_window"],
                "Tender Window": f"{facts['tender_period_days']} Business Days before Expiry",
                "Delivery Type": "Compulsory Delivery (Both Gold & Silver)",
                "Liquidity Phase": "Primary (Front Month)" if sym in ["GOLDM", "GOLDPETAL"] else "Secondary / Build-up",
                "History Available": "From 2025 listing" if sym == "GOLDTEN" else "Full Multi-Year History"
            })
        lc_df = pd.DataFrame(lifecycle_rows)
        st.dataframe(lc_df, hide_index=True, use_container_width=True)

    # 2. Expiry Schedule Timeline
    st.markdown("<br>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("### Contract Expiry & Tender Period Timeline")
        st.markdown('<p class="chart-caption-text">Timeline illustrating tender periods (highlighted warning zone) and final settlement expiry windows per month.</p>', unsafe_allow_html=True)
        
        timeline_data = [
            dict(Contract="GOLDM", Phase="Trading & Liquidity Build-Up", Start="2026-01-01", Finish="2026-01-28"),
            dict(Contract="GOLDM", Phase="Tender Period (No New Positions)", Start="2026-01-29", Finish="2026-02-02"),
            dict(Contract="GOLDM", Phase="Expiry Window", Start="2026-02-03", Finish="2026-02-05"),
            
            dict(Contract="GOLDTEN", Phase="Trading & Liquidity Build-Up", Start="2026-01-01", Finish="2026-01-21"),
            dict(Contract="GOLDTEN", Phase="Tender Period (No New Positions)", Start="2026-01-22", Finish="2026-01-26"),
            dict(Contract="GOLDTEN", Phase="Expiry Window", Start="2026-01-27", Finish="2026-01-31"),
            
            dict(Contract="GOLDGUINEA", Phase="Trading & Liquidity Build-Up", Start="2026-01-01", Finish="2026-01-21"),
            dict(Contract="GOLDGUINEA", Phase="Tender Period (No New Positions)", Start="2026-01-22", Finish="2026-01-26"),
            dict(Contract="GOLDGUINEA", Phase="Expiry Window", Start="2026-01-27", Finish="2026-01-31"),

            dict(Contract="GOLDPETAL", Phase="Trading & Liquidity Build-Up", Start="2026-01-01", Finish="2026-01-21"),
            dict(Contract="GOLDPETAL", Phase="Tender Period (No New Positions)", Start="2026-01-22", Finish="2026-01-26"),
            dict(Contract="GOLDPETAL", Phase="Expiry Window", Start="2026-01-27", Finish="2026-01-31"),
        ]
        
        df_timeline = pd.DataFrame(timeline_data)
        fig_timeline = px.timeline(
            df_timeline,
            x_start="Start",
            x_end="Finish",
            y="Contract",
            color="Phase",
            color_discrete_map={
                "Trading & Liquidity Build-Up": "#38BDF8",
                "Tender Period (No New Positions)": "#F59E0B",
                "Expiry Window": "#EF4444"
            },
            title="Monthly Tender & Expiry Calendar Lifecycle"
        )
        fig_timeline.update_layout(**get_layout_defaults(x_title="Date"))
        st.plotly_chart(fig_timeline, use_container_width=True)

        with st.expander("Explain Contract Lifecycle Rules"):
            st.write(
                "1. **Tender Window Risk**: During the 5-day tender period prior to expiry, open positions risk physical delivery assignment. Quantitative trading models must automatically exit or roll spread positions prior to entering the tender window.\n"
                "2. **GOLDTEN History Note**: GOLDTEN was introduced on MCX in 2025."
            )

if __name__ == "__main__":
    render()
