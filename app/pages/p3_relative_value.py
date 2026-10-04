"""
Page 3: Relative Value & Pairwise Spreads.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from assets.theme import init_page_theme, render_hero_banner
from data.loader import get_or_load_dataset
from core.relative_value import compute_pairwise_spreads, compute_cheap_expensive_matrix
from core.cost_model import calculate_roundtrip_cost_per_gram
from assets.plotly_theme import get_layout_defaults

def render():
    init_page_theme()
    df, _, is_synthetic = get_or_load_dataset()
    
    render_hero_banner(
        title="Relative Value & Pairwise Spreads",
        subtitle="Identifies cross-contract mispricing gaps and evaluates tradeability against cost friction",
        is_synthetic=is_synthetic
    )

    if df.empty:
        st.error("No dataset available.")
        return

    # Pair Selector
    pairs = [
        ("GOLDM", "GOLDPETAL"),
        ("GOLDM", "GOLDTEN"),
        ("GOLDM", "GOLDGUINEA"),
        ("GOLDTEN", "GOLDPETAL"),
        ("GOLDTEN", "GOLDGUINEA"),
        ("GOLDGUINEA", "GOLDPETAL"),
    ]
    pair_labels = [f"{p[0]} vs {p[1]}" for p in pairs]
    
    col_sel1, col_sel2, col_sel3 = st.columns([2, 1, 1])
    with col_sel1:
        selected_label = st.selectbox("Select Contract Pair for Spread Analysis", pair_labels)
        selected_pair = pairs[pair_labels.index(selected_label)]
    with col_sel2:
        lookback_window = st.number_input("Rolling Window (Days)", min_value=5, max_value=60, value=20)
    with col_sel3:
        z_threshold = st.number_input("Z-Score Threshold", min_value=0.5, max_value=3.0, value=1.5, step=0.1)

    spread_df = compute_pairwise_spreads(df, selected_pair, window=lookback_window)
    if spread_df.empty:
        st.warning("Insufficient data to compute spreads.")
        return

    # 1. Spread Chart Card
    with st.container(border=True):
        st.markdown(f"### Normalized Spread & Z-Score Bands ({selected_pair[0]} - {selected_pair[1]})")
        st.markdown('<p class="chart-caption-text">Price spread per gram (999 purity) shown with rolling mean and ±1.5 / ±2.0 Z-score bands.</p>', unsafe_allow_html=True)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=spread_df["Date"], y=spread_df["spread"],
            mode="lines", name="Per-Gram Spread (₹/g)",
            line=dict(color="#E8A317", width=2)
        ))
        fig.add_trace(go.Scatter(
            x=spread_df["Date"], y=spread_df["rolling_mean"],
            mode="lines", name="Rolling Mean",
            line=dict(color="#94A3B8", dash="dash", width=1.5)
        ))
        
        upper_band = spread_df["rolling_mean"] + z_threshold * spread_df["rolling_std"]
        lower_band = spread_df["rolling_mean"] - z_threshold * spread_df["rolling_std"]
        
        fig.add_trace(go.Scatter(
            x=spread_df["Date"], y=upper_band,
            mode="lines", name=f"+{z_threshold} std (Expensive)",
            line=dict(color="#EF4444", dash="dot", width=1)
        ))
        fig.add_trace(go.Scatter(
            x=spread_df["Date"], y=lower_band,
            mode="lines", name=f"-{z_threshold} std (Cheap)",
            line=dict(color="#10B981", dash="dot", width=1)
        ))
        
        fig.update_layout(**get_layout_defaults(
            title=f"Normalized Spread (₹/g): {selected_pair[0]} - {selected_pair[1]}",
            x_title="Date", y_title="Spread (₹ / g @ 999)"
        ))
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("Explain this chart"):
            st.write(
                "When the spread rises above the red upper band, Leg 1 is expensive relative to Leg 2 (short Leg 1 / long Leg 2). "
                "When it drops below the green lower band, Leg 1 is cheap relative to Leg 2 (long Leg 1 / short Leg 2)."
            )

    # 2. Heatmap Matrix
    st.markdown("<br>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("### Cross-Contract Cheap / Expensive Matrix (Z-Scores)")
        st.markdown('<p class="chart-caption-text">Matrix of current z-scores across all contract pairs. Red indicates row contract is expensive vs column; green indicates cheap.</p>', unsafe_allow_html=True)
        
        matrix = compute_cheap_expensive_matrix(df)
        fig_hm = px.imshow(
            matrix.astype(float),
            labels=dict(x="Leg 2 Contract", y="Leg 1 Contract", color="Z-Score"),
            x=matrix.columns,
            y=matrix.index,
            color_continuous_scale="RdYlGn_r",
            text_auto=True,
            aspect="auto"
        )
        fig_hm.update_layout(**get_layout_defaults(title="Relative Mispricing Matrix (Z-Score)"))
        st.plotly_chart(fig_hm, use_container_width=True)

    # 3. Today's Flagged Gaps vs Cost Threshold
    st.markdown("<br>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("### Today's Flagged Mispricing Gaps vs Cost Threshold")
        st.markdown('<p class="chart-caption-text">Evaluates raw per-gram gap against estimated transaction costs. Highlighted GREEN only if the gap survives trading friction.</p>', unsafe_allow_html=True)
        
        latest_rows = []
        for p in pairs:
            sp = compute_pairwise_spreads(df, p, window=lookback_window)
            if not sp.empty:
                last = sp.iloc[-1]
                raw_gap = abs(float(last["spread"]))
                leg1_p = float(last[f"Close_per_g_999_{p[0]}"])
                costs = calculate_roundtrip_cost_per_gram(leg1_p)
                roundtrip_cost = costs["total_cost_per_g"] * 2.0
                survives = raw_gap > roundtrip_cost
                
                latest_rows.append({
                    "Contract Pair": f"{p[0]} vs {p[1]}",
                    "Raw Spread (₹/g)": round(float(last["spread"]), 2),
                    "Abs Gap (₹/g)": round(raw_gap, 2),
                    "Z-Score": round(float(last["z_score"]), 2),
                    "Est. Roundtrip Cost (₹/g)": round(roundtrip_cost, 2),
                    "Survives Friction?": "YES (Tradeable)" if survives else "NO (Eaten by Costs)",
                    "Status Flag": last["signal_flag"]
                })
                
        gap_df = pd.DataFrame(latest_rows)
        st.dataframe(
            gap_df.style.map(
                lambda v: "background-color: rgba(16, 185, 129, 0.25); color: #34D399; font-weight: bold;" if "YES" in str(v)
                else ("background-color: rgba(239, 68, 68, 0.15); color: #F87171;" if "NO" in str(v) else ""),
                subset=["Survives Friction?"]
            ),
            hide_index=True,
            use_container_width=True
        )

if __name__ == "__main__":
    render()
