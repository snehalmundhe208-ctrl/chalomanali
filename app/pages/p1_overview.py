"""
Page 1: Overview & Hero Dashboard.
"""

import streamlit as st
import pandas as pd
import plotly.express as px

from assets.theme import init_page_theme, render_hero_banner
from data.loader import get_or_load_dataset
from core.verdict import evaluate_verdict
from core.backtest import run_walk_forward_backtest
from assets.plotly_theme import get_layout_defaults

def render():
    init_page_theme()
    
    # Load dataset
    df, _, is_synthetic = get_or_load_dataset()
    
    # 1. Hero Banner
    render_hero_banner(
        title="Commodity Derivatives Intelligence",
        subtitle="MCX Gold Futures Relative Value & Systematic Mispricing Dashboard",
        is_synthetic=is_synthetic
    )
    
    if df.empty:
        st.error("No dataset available.")
        return

    # Calculate metrics
    latest_date = df["Date"].max()
    num_contracts = df["Symbol"].nunique()
    
    # Run baseline walk-forward backtest for GOLDM vs GOLDPETAL
    bt_res = run_walk_forward_backtest(df, ("GOLDM", "GOLDPETAL"), z_entry=1.5, z_exit=0.2)
    metrics = bt_res["metrics"]
    verdict_info = evaluate_verdict(metrics, is_synthetic=is_synthetic)
    
    # 2. Row of 4 KPI Cards (using st.columns & st.metric / custom KPI markup)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            label="LATEST DATA DATE",
            value=str(latest_date),
            delta="MCX Bhavcopy",
            delta_color="off"
        )
    with col2:
        st.metric(
            label="ACTIVE CONTRACTS",
            value=f"{num_contracts} / 4",
            delta="GOLDM, TEN, GUINEA, PETAL",
            delta_color="off"
        )
    with col3:
        st.metric(
            label="NET BACKTEST RETURN",
            value=f"{metrics['net_return_pct']:.2f}%",
            delta=f"Sharpe: {metrics['sharpe_ratio']:.2f}",
            delta_color="normal" if metrics['net_return_pct'] > 0 else "inverse"
        )
    with col4:
        st.metric(
            label="PAIR MISPRICING SIGNALS",
            value=f"{metrics['total_trades']} Trades",
            delta=f"Hit Rate: {metrics['hit_rate_pct']:.1f}%",
            delta_color="normal" if metrics['hit_rate_pct'] >= 50 else "inverse"
        )

    # 3. Big Verdict Banner (Green for signal, Amber for marginal, Red for no edge)
    status_lower = verdict_info["status"].lower()
    if "signal found" in status_lower:
        box_class = "verdict-box-green"
        text_color = "#10B981"
    elif "marginal" in status_lower:
        box_class = "verdict-box-amber"
        text_color = "#F59E0B"
    else:
        box_class = "verdict-box-red"
        text_color = "#EF4444"

    st.markdown(
        f"""
        <div class="verdict-box {box_class}">
            <div class="verdict-title-text" style="color: {text_color};">
                Strategy Verdict: {verdict_info['full_label']}
            </div>
            <div class="verdict-reason-text">{verdict_info['reason']}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 4. What To Do Today Card inside st.container(border=True)
    with st.container(border=True):
        st.markdown("### 💡 What To Do Today")
        if "no persistent edge" in verdict_info["status"].lower():
            st.markdown(
                "**Recommendation**: **Stand Aside Today**. Mispricing spreads across contracts do not exceed the cost threshold "
                "(brokerage + exchange fees + bid-ask slippage). Rigor over signal frequency."
            )
        elif "marginal" in verdict_info["status"].lower():
            st.markdown(
                "**Recommendation**: **Monitor Spreads**. Small price gap detected between GOLDTEN and GOLDPETAL. "
                "Execution timing is critical due to market friction."
            )
        else:
            st.markdown(
                "**Recommendation**: **Actionable Relative Value Signal**. Execute Long GOLDM / Short GOLDPETAL spread at market open. "
                "Spread gap exceeds roundtrip transaction cost friction."
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # 5. Mini Price Chart inside st.container(border=True)
    with st.container(border=True):
        st.markdown("### Normalized Gold Futures Prices (₹ / gram @ 999 Purity)")
        st.markdown('<p class="chart-caption-text">Compares normalized daily close prices per gram across all 4 MCX gold contracts.</p>', unsafe_allow_html=True)
        
        front_contracts = df.sort_values(["Symbol", "Date", "ExpiryDate"]).groupby(["Symbol", "Date"]).first().reset_index()
        
        fig = px.line(
            front_contracts,
            x="Date",
            y="Close_per_g_999",
            color="Symbol",
            color_discrete_map={
                "GOLDM": "#E8A317",
                "GOLDTEN": "#38BDF8",
                "GOLDGUINEA": "#10B981",
                "GOLDPETAL": "#F43F5E"
            },
        )
        fig.update_layout(**get_layout_defaults(y_title="Price (₹ / gram @ 999)", x_title="Date"))
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("Explain this chart"):
            st.write(
                "Raw contract quotes differ because GOLDM is quoted per 10g at 995 purity, GOLDTEN per 10g at 999 purity, "
                "GOLDGUINEA per 8g, and GOLDPETAL per 1g. This chart normalizes every contract to a standardized **price per gram at 999 purity**, "
                "allowing direct apples-to-apples price comparison and identifying genuine relative mispricing gaps."
            )

if __name__ == "__main__":
    render()
