"""
Relative Value & Pairwise Spread Analytics Engine.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional

def compute_pairwise_spreads(
    df: pd.DataFrame,
    pair: Tuple[str, str],
    window: int = 20
) -> pd.DataFrame:
    """
    Computes normalized spread between two contracts on matching dates & matching expiry dates (or matching nearest expiry).
    Spread = Price_999(Leg1) - Price_999(Leg2)
    Also calculates rolling mean, rolling std, and rolling z-score.
    """
    leg1_sym, leg2_sym = pair
    
    # Filter for leg1 and leg2
    df_l1 = df[df["Symbol"] == leg1_sym].copy()
    df_l2 = df[df["Symbol"] == leg2_sym].copy()
    
    if df_l1.empty or df_l2.empty:
        return pd.DataFrame()
        
    # Ensure per-gram 999 column exists
    if "Close_per_g_999" not in df_l1.columns:
        from core.normalization import normalize_dataframe
        df_l1 = normalize_dataframe(df_l1)
        df_l2 = normalize_dataframe(df_l2)
        
    # Merge on Date and ExpiryDate to ensure matching expiry contracts
    merged = pd.merge(
        df_l1[["Date", "ExpiryDate", "Close_per_g_999", "Volume", "OpenInterest"]],
        df_l2[["Date", "ExpiryDate", "Close_per_g_999", "Volume", "OpenInterest"]],
        on=["Date", "ExpiryDate"],
        suffixes=(f"_{leg1_sym}", f"_{leg2_sym}")
    )
    
    # If merged on ExpiryDate is empty (e.g. GOLDM expiry windows differ from GOLDTEN/GOLDPETAL),
    # merge on Date matching the nearest expiry contract for each date.
    if merged.empty:
        # Sort by ExpiryDate per Date and pick front contract for each
        front_l1 = df_l1.sort_values("ExpiryDate").groupby("Date").first().reset_index()
        front_l2 = df_l2.sort_values("ExpiryDate").groupby("Date").first().reset_index()
        
        merged = pd.merge(
            front_l1[["Date", "ExpiryDate", "Close_per_g_999", "Volume", "OpenInterest"]],
            front_l2[["Date", "ExpiryDate", "Close_per_g_999", "Volume", "OpenInterest"]],
            on="Date",
            suffixes=(f"_{leg1_sym}", f"_{leg2_sym}")
        )
        
    if merged.empty:
        return pd.DataFrame()
        
    merged = merged.sort_values("Date").reset_index(drop=True)
    
    col_l1 = f"Close_per_g_999_{leg1_sym}"
    col_l2 = f"Close_per_g_999_{leg2_sym}"
    
    merged["spread"] = merged[col_l1] - merged[col_l2]
    
    # Rolling statistics (using expanding window for initial days to avoid NaN drops)
    merged["rolling_mean"] = merged["spread"].rolling(window=window, min_periods=5).mean()
    merged["rolling_std"] = merged["spread"].rolling(window=window, min_periods=5).std().fillna(1e-5).replace(0, 1e-5)
    
    merged["z_score"] = (merged["spread"] - merged["rolling_mean"]) / merged["rolling_std"]
    
    # Flags
    merged["signal_flag"] = "Fair Value"
    merged.loc[merged["z_score"] >= 1.5, "signal_flag"] = f"{leg1_sym} Expensive / {leg2_sym} Cheap"
    merged.loc[merged["z_score"] <= -1.5, "signal_flag"] = f"{leg1_sym} Cheap / {leg2_sym} Expensive"
    
    merged["Leg1"] = leg1_sym
    merged["Leg2"] = leg2_sym
    
    return merged

def compute_cheap_expensive_matrix(df: pd.DataFrame, target_date: Optional[str] = None) -> pd.DataFrame:
    """
    Computes cheap/expensive matrix across all 4 contracts on a specific date.
    Returns matrix of per-gram price differences and z-scores.
    """
    symbols = ["GOLDM", "GOLDTEN", "GOLDGUINEA", "GOLDPETAL"]
    matrix = pd.DataFrame(index=symbols, columns=symbols, dtype=float)
    
    if df.empty:
        return matrix
        
    for s1 in symbols:
        for s2 in symbols:
            if s1 == s2:
                matrix.loc[s1, s2] = 0.0
            else:
                sp_df = compute_pairwise_spreads(df, (s1, s2))
                if not sp_df.empty:
                    latest = sp_df.iloc[-1]
                    matrix.loc[s1, s2] = round(float(latest["z_score"]), 2)
                else:
                    matrix.loc[s1, s2] = np.nan
    return matrix
