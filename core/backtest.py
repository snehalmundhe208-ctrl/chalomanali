"""
Walk-Forward Relative Value Backtest Engine (No Look-Ahead Bias).

Rule: On day t, use ONLY data up to day t.
Signal generated at close of day t. Execution at day t+1.
Applies transaction costs, liquidity filter, and calendar bounds.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from core.normalization import normalize_dataframe
from core.cost_model import calculate_roundtrip_cost_per_gram

def run_walk_forward_backtest(
    df: pd.DataFrame,
    pair: Tuple[str, str],
    z_entry: float = 1.5,
    z_exit: float = 0.2,
    lookback_window: int = 20,
    custom_costs: Optional[Dict[str, float]] = None,
    min_volume: int = 5,
    min_oi: int = 10,
) -> Dict[str, Any]:
    """
    Executes a walk-forward pair trading backtest on normalized 999 gold prices per gram.
    
    Returns dictionary with:
      - equity_curve (DataFrame)
      - trade_log (DataFrame)
      - metrics (Dict)
    """
    leg1, leg2 = pair
    
    # Extract leg data
    df_l1 = df[df["Symbol"] == leg1].copy()
    df_l2 = df[df["Symbol"] == leg2].copy()
    
    if df_l1.empty or df_l2.empty:
        return _empty_backtest_result()
        
    if "Close_per_g_999" not in df_l1.columns:
        df_l1 = normalize_dataframe(df_l1)
        df_l2 = normalize_dataframe(df_l2)
        
    # Sort dates
    df_l1["Date"] = pd.to_datetime(df_l1["Date"])
    df_l2["Date"] = pd.to_datetime(df_l2["Date"])
    
    # Pick front contract per date
    front1 = df_l1.sort_values(["Date", "ExpiryDate"]).groupby("Date").first().reset_index()
    front2 = df_l2.sort_values(["Date", "ExpiryDate"]).groupby("Date").first().reset_index()
    
    merged = pd.merge(
        front1[["Date", "Close_per_g_999", "Volume", "OpenInterest"]],
        front2[["Date", "Close_per_g_999", "Volume", "OpenInterest"]],
        on="Date",
        suffixes=(f"_{leg1}", f"_{leg2}")
    ).sort_values("Date").reset_index(drop=True)
    
    if len(merged) < lookback_window + 2:
        return _empty_backtest_result()
        
    col_l1 = f"Close_per_g_999_{leg1}"
    col_l2 = f"Close_per_g_999_{leg2}"
    vol_l1 = f"Volume_{leg1}"
    vol_l2 = f"Volume_{leg2}"
    oi_l1 = f"OpenInterest_{leg1}"
    oi_l2 = f"OpenInterest_{leg2}"
    
    # Spread definition: Leg1 - Leg2
    merged["spread"] = merged[col_l1] - merged[col_l2]
    
    # Walk-forward loop to compute signals strictly up to day t
    n = len(merged)
    signals = np.zeros(n, dtype=int)  # 1 = Long Leg1/Short Leg2, -1 = Short Leg1/Long Leg2, 0 = Flat
    
    # Simulation state
    current_pos = 0  # Position held at close of day t
    trades: List[Dict[str, Any]] = []
    entry_idx = None
    entry_spread = 0.0
    entry_l1 = 0.0
    entry_l2 = 0.0
    
    # Daily equity tracking
    capital = 100000.0  # ₹100,000 baseline
    cumulative_pnl = 0.0
    daily_pnls = []
    equity_series = [capital]
    
    for i in range(n):
        date_t = merged.loc[i, "Date"]
        spread_t = merged.loc[i, "spread"]
        p1_t = merged.loc[i, col_l1]
        p2_t = merged.loc[i, col_l2]
        
        # Check liquidity filter for day t
        liquid = (
            merged.loc[i, vol_l1] >= min_volume and
            merged.loc[i, vol_l2] >= min_volume and
            merged.loc[i, oi_l1] >= min_oi and
            merged.loc[i, oi_l2] >= min_oi
        )
        
        # Walk-forward signal calculation using window UP TO index i (inclusive)
        if i >= lookback_window - 1:
            historical_spreads = merged.loc[max(0, i - lookback_window + 1):i, "spread"]
            mean_t = historical_spreads.mean()
            std_t = historical_spreads.std()
            if std_t is None or np.isnan(std_t) or std_t == 0:
                std_t = 1e-5
            z_score_t = (spread_t - mean_t) / std_t
        else:
            z_score_t = 0.0
            
        # Position execution happens on day t+1 based on signal set at end of day t
        # If we have a position entering into day t, calculate daily mark-to-market PnL
        if i > 0 and current_pos != 0:
            prev_spread = merged.loc[i-1, "spread"]
            daily_raw = current_pos * (spread_t - prev_spread)
            cumulative_pnl += daily_raw
        
        daily_pnls.append(cumulative_pnl)
        equity_series.append(capital + cumulative_pnl)
        
        # Signal logic at close of day t (for execution starting at t+1)
        next_pos = current_pos
        if liquid:
            if current_pos == 0:
                if z_score_t >= z_entry:
                    next_pos = -1  # Short Leg1, Long Leg2 (spread is overpriced)
                    entry_idx = i
                    entry_spread = spread_t
                    entry_l1, entry_l2 = p1_t, p2_t
                elif z_score_t <= -z_entry:
                    next_pos = 1   # Long Leg1, Short Leg2 (spread is underpriced)
                    entry_idx = i
                    entry_spread = spread_t
                    entry_l1, entry_l2 = p1_t, p2_t
            else:
                # Exit condition
                if (current_pos == 1 and z_score_t >= -z_exit) or (current_pos == -1 and z_score_t <= z_exit):
                    # Close trade
                    exit_spread = spread_t
                    raw_pnl_per_g = current_pos * (exit_spread - entry_spread)
                    
                    # Roundtrip transaction costs
                    costs1 = calculate_roundtrip_cost_per_gram(entry_l1, custom_costs)
                    costs2 = calculate_roundtrip_cost_per_gram(entry_l2, custom_costs)
                    total_costs_per_g = (costs1["total_cost_per_g"] + costs2["total_cost_per_g"]) / 2.0
                    
                    net_pnl_per_g = raw_pnl_per_g - total_costs_per_g
                    holding_days = i - entry_idx
                    
                    trades.append({
                        "entry_date": str(merged.loc[entry_idx, "Date"].strftime("%Y-%m-%d")),
                        "exit_date": str(date_t.strftime("%Y-%m-%d")),
                        "position": "Long Spread" if current_pos == 1 else "Short Spread",
                        "entry_spread": round(entry_spread, 2),
                        "exit_spread": round(exit_spread, 2),
                        "raw_pnl_per_g": round(raw_pnl_per_g, 2),
                        "cost_per_g": round(total_costs_per_g, 2),
                        "net_pnl_per_g": round(net_pnl_per_g, 2),
                        "holding_days": holding_days,
                        "win": net_pnl_per_g > 0
                    })
                    
                    # Apply cost deduction to cumulative pnl
                    cumulative_pnl -= total_costs_per_g
                    next_pos = 0
                    entry_idx = None

        current_pos = next_pos
        signals[i] = current_pos
        
    merged["signal"] = signals
    merged["cumulative_pnl"] = daily_pnls
    merged["equity"] = equity_series[1:]
    
    # Performance metrics
    trade_df = pd.DataFrame(trades)
    metrics = _compute_metrics(merged, trade_df, capital)
    
    return {
        "equity_curve": merged,
        "trade_log": trade_df,
        "metrics": metrics,
    }

def _compute_metrics(merged: pd.DataFrame, trade_df: pd.DataFrame, initial_capital: float) -> Dict[str, Any]:
    """
    Computes key performance metrics for the walk-forward backtest.
    """
    if merged.empty:
        return _empty_metrics()
        
    net_pnl_total = merged["cumulative_pnl"].iloc[-1]
    net_return_pct = (net_pnl_total / 1000.0)  # Standardized per gram return %
    
    # Calculate Drawdown
    equity = merged["equity"]
    peak = equity.cummax()
    drawdown = (equity - peak) / peak
    max_drawdown = float(drawdown.min() * 100.0)
    
    # Daily returns & Sharpe
    daily_ret = merged["cumulative_pnl"].diff().fillna(0)
    mean_ret = daily_ret.mean()
    std_ret = daily_ret.std()
    
    if std_ret > 0:
        sharpe = float((mean_ret / std_ret) * np.sqrt(252))
    else:
        sharpe = 0.0
        
    total_trades = len(trade_df)
    if total_trades > 0:
        winning_trades = int(trade_df["win"].sum())
        hit_rate = float(winning_trades / total_trades * 100.0)
        avg_trade_pnl = float(trade_df["net_pnl_per_g"].mean())
    else:
        winning_trades = 0
        hit_rate = 0.0
        avg_trade_pnl = 0.0
        
    return {
        "net_pnl_total": round(net_pnl_total, 2),
        "net_return_pct": round(net_return_pct, 2),
        "sharpe_ratio": round(sharpe, 2),
        "max_drawdown_pct": round(max_drawdown, 2),
        "total_trades": total_trades,
        "hit_rate_pct": round(hit_rate, 1),
        "avg_trade_pnl_per_g": round(avg_trade_pnl, 2),
    }

def _empty_backtest_result() -> Dict[str, Any]:
    return {
        "equity_curve": pd.DataFrame(),
        "trade_log": pd.DataFrame(),
        "metrics": _empty_metrics(),
    }

def _empty_metrics() -> Dict[str, Any]:
    return {
        "net_pnl_total": 0.0,
        "net_return_pct": 0.0,
        "sharpe_ratio": 0.0,
        "max_drawdown_pct": 0.0,
        "total_trades": 0,
        "hit_rate_pct": 0.0,
        "avg_trade_pnl_per_g": 0.0,
    }
