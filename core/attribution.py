"""
Attribution & Strategy vs Benchmark Decomposition.
Decomposes total return into gold market beta vs pure relative value alpha.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any

def compute_attribution(
    backtest_equity: pd.DataFrame,
    df_raw: pd.DataFrame
) -> Dict[str, Any]:
    """
    Decomposes strategy returns into market buy-and-hold benchmark vs spread alpha.
    """
    if backtest_equity.empty or df_raw.empty:
        return {
            "strategy_return_pct": 0.0,
            "gold_benchmark_return_pct": 0.0,
            "alpha_pct": 0.0,
            "correlation": 0.0,
        }
        
    # Get Gold benchmark (GOLDM front contract per gram)
    goldm = df_raw[df_raw["Symbol"] == "GOLDM"].copy()
    if "Close_per_g_999" not in goldm.columns:
        from core.normalization import normalize_dataframe
        goldm = normalize_dataframe(goldm)
        
    goldm["Date"] = pd.to_datetime(goldm["Date"])
    bm_series = goldm.sort_values("Date").groupby("Date")["Close_per_g_999"].first().reset_index()
    
    merged = pd.merge(
        backtest_equity[["Date", "equity", "cumulative_pnl"]],
        bm_series,
        on="Date",
        how="inner"
    ).sort_values("Date")
    
    if len(merged) < 2:
        return {
            "strategy_return_pct": 0.0,
            "gold_benchmark_return_pct": 0.0,
            "alpha_pct": 0.0,
            "correlation": 0.0,
        }
        
    strat_init = merged["equity"].iloc[0]
    strat_final = merged["equity"].iloc[-1]
    strat_ret = ((strat_final - strat_init) / strat_init) * 100.0
    
    bm_init = merged["Close_per_g_999"].iloc[0]
    bm_final = merged["Close_per_g_999"].iloc[-1]
    bm_ret = ((bm_final - bm_init) / bm_init) * 100.0
    
    alpha = strat_ret - bm_ret
    
    # Correlation between daily strategy changes and benchmark daily changes
    strat_daily = merged["equity"].pct_change().dropna()
    bm_daily = merged["Close_per_g_999"].pct_change().dropna()
    
    if len(strat_daily) > 2 and len(bm_daily) > 2:
        corr = float(strat_daily.corr(bm_daily))
        if np.isnan(corr):
            corr = 0.0
    else:
        corr = 0.0
        
    return {
        "strategy_return_pct": round(strat_ret, 2),
        "gold_benchmark_return_pct": round(bm_ret, 2),
        "alpha_pct": round(alpha, 2),
        "correlation": round(corr, 3),
    }
