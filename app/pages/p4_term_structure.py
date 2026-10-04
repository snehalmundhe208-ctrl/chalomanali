"""
Page 4: Term Structure & Carry Decomposition.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from assets.theme import init_page_theme, render_hero_banner
from data.loader import get_or_load_dataset
from core.term_structure import compute_futures_curve, decompose_carry_and_shift
from assets.plotly_theme import get_layout_defaults

def render():
    init_page_theme()
    df, _, is_synthetic = get_or_load_dataset()
    
    render_hero_banner(
        title="Term Structure & Carry Decomposition",
        subtitle="Decomposes daily price changes into mechanical roll-down carry toward expiry versus genuine curve shifts",
        is_synthetic=is_synthetic
    )

    if df.empty:
        st.error("No dataset available.")
        return

    # 1. Futures Curve Card
    with st.container(border=True):
        st.markdown("### Futures Curve by Trade Date")
        st.markdown('<p class="chart-caption-text">Inspects the shape of the normalized gold futures curve across contract expiries for a selected date.</p>', unsafe_allow_html=True)
        
        available_dates = sorted(df["Date"].unique())
        selected_date = st.select_slider("Select Trade Date", options=available_dates, value=available_dates[-1])
        
        curve_df = compute_futures_curve(df, selected_date)
        if not curve_df.empty:
            fig_curve = px.line(
                curve_df,
                x="ExpiryDate",
                y="Close_per_g_999",
                color="Symbol",
                markers=True,
                title=f"Normalized Futures Curve on {selected_date}"
            )
            fig_curve.update_layout(**get_layout_defaults(x_title="Expiry Date", y_title="Price (₹ / gram @ 999)"))
            st.plotly_chart(fig_curve, use_container_width=True)
        else:
            st.info(f"No active contracts recorded for {selected_date}.")

        with st.expander("Explain this chart"):
            st.write(
                "The futures curve shows prices of contracts with different expiry dates on a single trade date. "
                "An upward-sloping curve (contango) means distant expiries trade at a premium, representing net cost of carry."
            )

    # 2. Roll-Down Carry vs Curve Shift Decomposition
    st.markdown("<br>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("### Roll-Down Carry vs Curve Shift Decomposition")
        st.markdown('<p class="chart-caption-text">Decomposes daily price changes for a contract into mechanical roll-down vs overall curve shift.</p>', unsafe_allow_html=True)
        
        col_sym, _ = st.columns([2, 2])
        with col_sym:
            sym_selected = st.selectbox("Select Contract for Carry Decomposition", ["GOLDM", "GOLDTEN", "GOLDGUINEA", "GOLDPETAL"])
            
        decomp_df = decompose_carry_and_shift(df, sym_selected)
        
        if not decomp_df.empty:
            fig_decomp = go.Figure()
            fig_decomp.add_trace(go.Bar(
                x=decomp_df["Date"], y=decomp_df["roll_down_carry"],
                name="Roll-Down Carry (₹/g)", marker_color="#10B981"
            ))
            fig_decomp.add_trace(go.Bar(
                x=decomp_df["Date"], y=decomp_df["curve_shift"],
                name="Curve Shift (₹/g)", marker_color="#38BDF8"
            ))
            fig_decomp.add_trace(go.Scatter(
                x=decomp_df["Date"], y=decomp_df["total_daily_change"],
                name="Total Change (₹/g)", line=dict(color="#E8A317", width=2)
            ))
            
            fig_decomp.update_layout(**get_layout_defaults(
                title=f"Daily Price Change Decomposition: {sym_selected}",
                x_title="Date", y_title="Daily Change (₹ / g)"
            ), barmode="relative")
            st.plotly_chart(fig_decomp, use_container_width=True)

        with st.expander("Explain Carry Decomposition"):
            st.write(
                "Total Daily Change = Roll-Down Carry + Curve Shift.\n"
                "- **Roll-Down Carry**: PnL captured by holding a contract as it rolls down a sloped futures curve toward expiry.\n"
                "- **Curve Shift**: Macro shift in the overall level or slope of the gold futures curve."
            )

if __name__ == "__main__":
    render()
