"""
Term Structure & Carry Analytics Engine.
Decomposes daily price changes into roll-down return vs curve shift.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple

def compute_futures_curve(df: pd.DataFrame, target_date: str) -> pd.DataFrame:
    """
    Returns the futures curve (price per gram 999 vs expiry date / days to expiry) for a given trade date.
    """
    if df.empty:
        return pd.DataFrame()
        
    df_date = df[df["Date"].astype(str) == str(target_date)].copy()
    if df_date.empty:
        return pd.DataFrame()
        
    if "Close_per_g_999" not in df_date.columns:
        from core.normalization import normalize_dataframe
        df_date = normalize_dataframe(df_date)
        
    df_date["Date"] = pd.to_datetime(df_date["Date"])
    df_date["ExpiryDate"] = pd.to_datetime(df_date["ExpiryDate"])
    df_date["days_to_expiry"] = (df_date["ExpiryDate"] - df_date["Date"]).dt.days
    
    # Filter non-expired
    df_date = df_date[df_date["days_to_expiry"] >= 0].sort_values("days_to_expiry")
    return df_date

def decompose_carry_and_shift(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """
    Decomposes daily price change for a contract into:
    1. Roll-down carry (moving down the sloped futures curve toward expiry)
    2. Curve shift (parallel / slope shift in the underlying curve level)
    """
    df_sym = df[df["Symbol"] == symbol].copy()
    if df_sym.empty:
        return pd.DataFrame()
        
    if "Close_per_g_999" not in df_sym.columns:
        from core.normalization import normalize_dataframe
        df_sym = normalize_dataframe(df_sym)
        
    df_sym["Date"] = pd.to_datetime(df_sym["Date"])
    df_sym["ExpiryDate"] = pd.to_datetime(df_sym["ExpiryDate"])
    df_sym["days_to_expiry"] = (df_sym["ExpiryDate"] - df_sym["Date"]).dt.days
    
    # Sort by expiry then date
    df_sym = df_sym.sort_values(["ExpiryDate", "Date"]).reset_index(drop=True)
    
    df_sym["total_daily_change"] = df_sym.groupby("ExpiryDate")["Close_per_g_999"].diff()
    df_sym["dte_change"] = df_sym.groupby("ExpiryDate")["days_to_expiry"].diff()
    
    # Estimate slope (price diff per day to expiry)
    # Roll-down estimate = slope * days_passed
    df_sym["price_slope"] = df_sym.groupby("Date")["Close_per_g_999"].diff() / df_sym.groupby("Date")["days_to_expiry"].diff()
    df_sym["price_slope"] = df_sym["price_slope"].fillna(0.0)
    
    df_sym["roll_down_carry"] = df_sym["price_slope"] * df_sym["dte_change"].abs().fillna(0)
    df_sym["curve_shift"] = df_sym["total_daily_change"] - df_sym["roll_down_carry"]
    
    # Fill NAs
    df_sym["total_daily_change"] = df_sym["total_daily_change"].fillna(0.0)
    df_sym["roll_down_carry"] = df_sym["roll_down_carry"].fillna(0.0)
    df_sym["curve_shift"] = df_sym["curve_shift"].fillna(0.0)
    
    return df_sym
