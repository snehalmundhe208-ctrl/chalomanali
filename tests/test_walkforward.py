"""
Unit tests for walk-forward backtest loop.
Contains strict NO LOOK-AHEAD BIAS test.
"""

import pytest
import pandas as pd
import numpy as np
from data.synthetic import generate_synthetic_bhavcopy
from core.normalization import normalize_dataframe
from core.backtest import run_walk_forward_backtest

def test_no_lookahead_bias():
    """
    CRITICAL TEST: Proves that signals generated at day t DO NOT CHANGE when future rows (t+1, t+2...) are altered.
    """
    # 1. Run backtest on base dataset
    df_base = generate_synthetic_bhavcopy(num_days=60, seed=42)
    df_norm_base = normalize_dataframe(df_base)
    
    res_base = run_walk_forward_backtest(df_norm_base, ("GOLDM", "GOLDPETAL"), lookback_window=10)
    signals_base = res_base["equity_curve"]["signal"].copy()
    
    # 2. Pick a target cutoff day t = 35
    cutoff_idx = 35
    
    # 3. Create a mutated dataset where future rows (index > cutoff_idx) are heavily altered with random noise
    df_mutated = df_norm_base.copy()
    mask_future = df_mutated.index > (cutoff_idx * 4)  # Multi-row contract offset
    df_mutated.loc[mask_future, "Close"] = df_mutated.loc[mask_future, "Close"] * 2.5
    df_mutated.loc[mask_future, "Close_per_g_999"] = df_mutated.loc[mask_future, "Close_per_g_999"] * 2.5
    
    res_mutated = run_walk_forward_backtest(df_mutated, ("GOLDM", "GOLDPETAL"), lookback_window=10)
    signals_mutated = res_mutated["equity_curve"]["signal"].copy()
    
    # Compare signals up to day cutoff_idx
    signals_base_cutoff = signals_base.iloc[:cutoff_idx].tolist()
    signals_mutated_cutoff = signals_mutated.iloc[:cutoff_idx].tolist()
    
    assert signals_base_cutoff == signals_mutated_cutoff, "Look-ahead bias detected! Signal at day t changed after altering future data."

def test_walkforward_backtest_execution():
    df = generate_synthetic_bhavcopy(num_days=80, seed=42)
    df_norm = normalize_dataframe(df)
    
    res = run_walk_forward_backtest(df_norm, ("GOLDM", "GOLDPETAL"), lookback_window=15)
    
    assert "equity_curve" in res
    assert "trade_log" in res
    assert "metrics" in res
    metrics = res["metrics"]
    assert "sharpe_ratio" in metrics
    assert "max_drawdown_pct" in metrics
