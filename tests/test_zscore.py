"""
Unit tests for relative value spreads, rolling z-scores, and cheap/expensive matrix.
"""

import pytest
import pandas as pd
import numpy as np
from data.synthetic import generate_synthetic_bhavcopy
from core.normalization import normalize_dataframe
from core.relative_value import compute_pairwise_spreads, compute_cheap_expensive_matrix

def test_pairwise_spreads_calculation():
    df = generate_synthetic_bhavcopy(num_days=30, seed=42)
    df_norm = normalize_dataframe(df)
    
    spread_df = compute_pairwise_spreads(df_norm, ("GOLDM", "GOLDPETAL"), window=10)
    
    assert not spread_df.empty
    assert "spread" in spread_df.columns
    assert "z_score" in spread_df.columns
    assert "signal_flag" in spread_df.columns
    assert len(spread_df) > 0

def test_cheap_expensive_matrix():
    df = generate_synthetic_bhavcopy(num_days=30, seed=42)
    df_norm = normalize_dataframe(df)
    
    matrix = compute_cheap_expensive_matrix(df_norm)
    assert matrix.shape == (4, 4)
    assert matrix.loc["GOLDM", "GOLDM"] == 0.0
    assert not np.isnan(matrix.loc["GOLDM", "GOLDPETAL"])
