"""
Page 2: Contract Explorer & Mechanics.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from assets.theme import init_page_theme, render_hero_banner
from core.config import CONTRACT_FACTS
from data.loader import get_or_load_dataset
from assets.plotly_theme import get_layout_defaults

def render():
    init_page_theme()
    df, _, is_synthetic = get_or_load_dataset()
    
    render_hero_banner(
        title="Contract Explorer & Mechanics",
        subtitle="MCX Gold Futures contract specifications and step-by-step price normalization math",
        is_synthetic=is_synthetic
    )

    # 1. Contract Specifications Table
    with st.container(border=True):
        st.markdown("### MCX Contract Specifications Matrix")
        table_data = []
        for sym, facts in CONTRACT_FACTS.items():
            table_data.append({
                "Contract Symbol": sym,
                "Trading Unit": f"{facts['trading_unit_grams']} g",
                "Price Quoted Per": f"{facts['quote_unit_grams']} g",
                "Purity (Fineness)": f"{facts['purity']} / 1000",
                "Expiry Window": facts["expiry_window"],
                "Tender Period": f"{facts['tender_period_days']} Days",
                "Notes": facts.get("description", "")
            })
        specs_df = pd.DataFrame(table_data)
        st.dataframe(specs_df, hide_index=True, use_container_width=True)

    # 2. Step-by-step Worked Example
    st.markdown("<br>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("### 🧮 Step-by-Step Normalization Worked Example")
        st.markdown(
            """
            <div class="explainer-box">
                <p>Suppose <strong>GOLDM</strong> is quoted at <strong>₹72,000 per 10g</strong> (995 purity) and <strong>GOLDTEN</strong> is quoted at <strong>₹72,300 per 10g</strong> (999 purity).</p>
                <ul>
                    <li><strong>Naïve Raw Comparison:</strong> ₹72,300 - ₹72,000 = <strong>₹300 per 10g gap</strong> (misleading ₹30/g apparent arbitrage!).</li>
                    <li><strong>Step 1: Calculate raw price per gram:</strong>
                        <ul>
                            <li>GOLDM raw per gram = ₹72,000 / 10 = ₹7,200.00 / g</li>
                            <li>GOLDTEN raw per gram = ₹72,300 / 10 = ₹7,230.00 / g</li>
                        </ul>
                    </li>
                    <li><strong>Step 2: Adjust GOLDM for 999 purity:</strong>
                        <ul>
                            <li>GOLDM @ 999 purity = ₹7,200 × (999 / 995) = <strong>₹7,228.9447 / g</strong></li>
                        </ul>
                    </li>
                    <li><strong>True Normalized Gap:</strong> ₹7,230.00 - ₹7,228.94 = <strong>₹1.06 / g</strong> (not ₹30/g!).</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True
        )

    # 3. Dual Chart (Before vs After Normalization)
    if not df.empty:
        st.markdown("<br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("### Before vs After Normalization Comparison")
            st.markdown('<p class="chart-caption-text">Left: Unadjusted raw quotes. Right: Standardized ₹ / gram @ 999 purity.</p>', unsafe_allow_html=True)
            
            front_contracts = df.sort_values(["Symbol", "Date", "ExpiryDate"]).groupby(["Symbol", "Date"]).first().reset_index()
            
            fig = make_subplots(
                rows=1, cols=2,
                subplot_titles=("Raw Quoted Prices (Mixed Units)", "Normalized Prices (₹ / g @ 999 Purity)")
            )
            
            symbols = ["GOLDM", "GOLDTEN", "GOLDGUINEA", "GOLDPETAL"]
            colors = {"GOLDM": "#E8A317", "GOLDTEN": "#38BDF8", "GOLDGUINEA": "#10B981", "GOLDPETAL": "#F43F5E"}
            
            for sym in symbols:
                sub_df = front_contracts[front_contracts["Symbol"] == sym]
                if not sub_df.empty:
                    fig.add_trace(
                        go.Scatter(x=sub_df["Date"], y=sub_df["Close"], name=sym, line=dict(color=colors[sym])),
                        row=1, col=1
                    )
                    fig.add_trace(
                        go.Scatter(x=sub_df["Date"], y=sub_df["Close_per_g_999"], name=f"{sym} (999)", line=dict(color=colors[sym]), showlegend=False),
                        row=1, col=2
                    )
                    
            fig.update_layout(**get_layout_defaults())
            fig.update_yaxes(title_text="Raw Quote (₹)", row=1, col=1)
            fig.update_yaxes(title_text="Normalized Price (₹ / g @ 999)", row=1, col=2)
            st.plotly_chart(fig, use_container_width=True)

            with st.expander("Explain this chart"):
                st.write(
                    "The raw quoted price chart on the left appears disjointed because contracts use different quote bases. "
                    "The normalized chart on the right brings all contracts onto a common baseline (₹ / gram at 999 purity)."
                )

if __name__ == "__main__":
    render()
