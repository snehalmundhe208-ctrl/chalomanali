"""
Page 5: Walk-Forward Backtest Lab & Sensitivity Engine.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from assets.theme import init_page_theme, render_hero_banner
from data.loader import get_or_load_dataset
from core.backtest import run_walk_forward_backtest
from core.attribution import compute_attribution
from core.verdict import evaluate_verdict
from core.cost_model import calculate_roundtrip_cost_per_gram
from assets.plotly_theme import get_layout_defaults

def render():
    init_page_theme()
    df, _, is_synthetic = get_or_load_dataset()
    
    render_hero_banner(
        title="Walk-Forward Backtest Lab",
        subtitle="Simulates pair trading execution strictly walk-forward ($t \\to t+1$, no look-ahead bias) with transaction costs and liquidity filters",
        is_synthetic=is_synthetic
    )
    
    if df.empty:
        st.error("No dataset available.")
        return

    # Sidebar Controls
    st.sidebar.markdown("### Backtest Controls")
    pairs = [
        ("GOLDM", "GOLDPETAL"),
        ("GOLDM", "GOLDTEN"),
        ("GOLDM", "GOLDGUINEA"),
        ("GOLDTEN", "GOLDPETAL"),
        ("GOLDTEN", "GOLDGUINEA"),
        ("GOLDGUINEA", "GOLDPETAL"),
    ]
    pair_labels = [f"{p[0]} vs {p[1]}" for p in pairs]
    selected_label = st.sidebar.selectbox("Strategy Contract Pair", pair_labels)
    selected_pair = pairs[pair_labels.index(selected_label)]
    
    z_entry = st.sidebar.slider("Z-Score Entry Threshold", min_value=0.8, max_value=3.0, value=1.5, step=0.1)
    z_exit = st.sidebar.slider("Z-Score Exit Threshold", min_value=0.0, max_value=1.0, value=0.2, step=0.1)
    lookback = st.sidebar.slider("Rolling Window (Days)", min_value=10, max_value=60, value=20)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Cost & Friction Model")
    slippage_input = st.sidebar.slider("Slippage (₹ / gram)", min_value=0.0, max_value=3.0, value=0.50, step=0.10)
    brokerage_pct = st.sidebar.slider("Brokerage Fee (%)", min_value=0.0, max_value=0.05, value=0.01, step=0.005) / 100.0
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Liquidity Filter")
    min_vol = st.sidebar.number_input("Min Volume (Contracts)", min_value=0, max_value=500, value=5)
    min_oi = st.sidebar.number_input("Min Open Interest", min_value=0, max_value=1000, value=10)

    custom_costs = {
        "slippage_per_gram": slippage_input,
        "brokerage_pct": brokerage_pct,
    }

    # Run Walk-Forward Backtest
    bt_res = run_walk_forward_backtest(
        df,
        selected_pair,
        z_entry=z_entry,
        z_exit=z_exit,
        lookback_window=lookback,
        custom_costs=custom_costs,
        min_volume=min_vol,
        min_oi=min_oi
    )
    
    equity_df = bt_res["equity_curve"]
    trade_df = bt_res["trade_log"]
    metrics = bt_res["metrics"]
    
    verdict_info = evaluate_verdict(metrics, is_synthetic=is_synthetic)
    
    # Render Verdict Banner
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

    # Top Metric Tiles
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Net Backtest Return", f"{metrics['net_return_pct']:.2f}%", help="After all transaction costs and slippage")
    c2.metric("Sharpe Ratio", f"{metrics['sharpe_ratio']:.2f}", help="Annualized risk-adjusted return")
    c3.metric("Max Drawdown", f"{metrics['max_drawdown_pct']:.2f}%")
    c4.metric("Hit Rate", f"{metrics['hit_rate_pct']:.1f}%")
    c5.metric("Total Trades Executed", f"{metrics['total_trades']}")

    # 1. Equity Curve Card
    st.markdown("<br>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("### Strategy Equity Curve vs Buy-and-Hold Gold Benchmark")
        st.markdown('<p class="chart-caption-text">Compares net strategy portfolio growth (starting ₹100,000 baseline) against underlying Gold spot benchmark.</p>', unsafe_allow_html=True)
        
        attr_info = compute_attribution(equity_df, df)
        if not equity_df.empty:
            fig_eq = go.Figure()
            fig_eq.add_trace(go.Scatter(
                x=equity_df["Date"], y=equity_df["equity"],
                mode="lines", name="Strategy Equity (Net after Costs)",
                line=dict(color="#E8A317", width=2.5)
            ))
            
            goldm_df = df[df["Symbol"] == "GOLDM"].sort_values("Date").groupby("Date").first().reset_index()
            goldm_merged = pd.merge(equity_df[["Date"]], goldm_df[["Date", "Close_per_g_999"]], on="Date", how="left").ffill()
            if not goldm_merged.empty:
                bm_init = goldm_merged["Close_per_g_999"].iloc[0]
                goldm_merged["bm_equity"] = 100000.0 * (goldm_merged["Close_per_g_999"] / bm_init)
                fig_eq.add_trace(go.Scatter(
                    x=goldm_merged["Date"], y=goldm_merged["bm_equity"],
                    mode="lines", name="Gold Buy-and-Hold Benchmark",
                    line=dict(color="#38BDF8", dash="dash", width=1.5)
                ))
                
            fig_eq.update_layout(**get_layout_defaults(y_title="Portfolio Value (₹)", x_title="Date"))
            st.plotly_chart(fig_eq, use_container_width=True)

    # 2. Drawdown Plot Card
    if not equity_df.empty:
        st.markdown("<br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("### Strategy Peak-to-Trough Drawdown (%)")
            equity_series = equity_df["equity"]
            peak = equity_series.cummax()
            drawdown_series = ((equity_series - peak) / peak) * 100.0
            
            fig_dd = px.area(
                x=equity_df["Date"], y=drawdown_series,
                color_discrete_sequence=["#EF4444"]
            )
            fig_dd.update_layout(**get_layout_defaults(y_title="Drawdown (%)", x_title="Date"))
            st.plotly_chart(fig_dd, use_container_width=True)

    # 3. Cost Sensitivity Card
    st.markdown("<br>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("### Cost Sensitivity Analysis: Net Return vs Transaction Friction")
        st.markdown('<p class="chart-caption-text">Demonstrates how net strategy returns decay as transaction costs (slippage/brokerage) increase from ₹0.0 to ₹3.0 per gram.</p>', unsafe_allow_html=True)
        
        cost_steps = np.linspace(0.0, 3.0, 10)
        sensitivity_results = []
        for c_step in cost_steps:
            step_costs = {"slippage_per_gram": c_step, "brokerage_pct": brokerage_pct}
            res_step = run_walk_forward_backtest(
                df, selected_pair, z_entry=z_entry, z_exit=z_exit,
                lookback_window=lookback, custom_costs=step_costs
            )
            m_step = res_step["metrics"]
            sensitivity_results.append({
                "Slippage (₹/g)": round(c_step, 2),
                "Net Return (%)": m_step["net_return_pct"],
                "Sharpe Ratio": m_step["sharpe_ratio"]
            })
            
        sens_df = pd.DataFrame(sensitivity_results)
        fig_sens = px.line(
            sens_df, x="Slippage (₹/g)", y=["Net Return (%)", "Sharpe Ratio"],
            markers=True,
            color_discrete_map={"Net Return (%)": "#E8A317", "Sharpe Ratio": "#38BDF8"}
        )
        fig_sens.add_hline(y=0.0, line_dash="dash", line_color="#EF4444", annotation_text="Breakeven Threshold")
        fig_sens.update_layout(**get_layout_defaults(x_title="Slippage (₹ per gram)", y_title="Performance Metric"))
        st.plotly_chart(fig_sens, use_container_width=True)

    # 4. Trade Log Card
    st.markdown("<br>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("### Walk-Forward Executed Trade Log")
        st.markdown('<p class="chart-caption-text">Detailed log of executed trades with entry/exit spreads, holding periods, and net PnL after cost deductions.</p>', unsafe_allow_html=True)
        
        if not trade_df.empty:
            st.dataframe(
                trade_df.style.map(
                    lambda v: "color: #34D399; font-weight: bold;" if v is True
                    else ("color: #F87171;" if v is False else ""),
                    subset=["win"]
                ),
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("No trades executed for the selected pair and z-score entry criteria.")

if __name__ == "__main__":
    render()
