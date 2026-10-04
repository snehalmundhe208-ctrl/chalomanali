"""
Price Normalization Module for MCX Gold Futures Contracts.
"""

import pandas as pd
import numpy as np
from typing import Union, Dict
from core.config import CONTRACT_FACTS, TARGET_PURITY

def normalize_price(price: float, symbol: str) -> float:
    """
    Normalizes a contract price to per-gram price at 999 purity.
    
    Formula:
      1. per_gram_raw = price / quote_unit_grams
      2. per_gram_999 = per_gram_raw * (999 / contract_purity)
    """
    symbol_clean = str(symbol).strip().upper()
    if symbol_clean not in CONTRACT_FACTS:
        raise ValueError(f"Unknown contract symbol: {symbol}")
    
    facts = CONTRACT_FACTS[symbol_clean]
    quote_grams = facts["quote_unit_grams"]
    purity = facts["purity"]
    
    per_gram_raw = price / quote_grams
    per_gram_999 = per_gram_raw * (TARGET_PURITY / purity)
    return round(per_gram_999, 4)

def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds normalized price columns (Close_per_g_999, Open_per_g_999, etc.) to a DataFrame.
    DataFrame must contain 'Symbol' and price columns ('Close', 'Open', 'High', 'Low').
    """
    if df.empty:
        return df
    
    res = df.copy()
    
    # Ensure symbol column is clean
    res["Symbol"] = res["Symbol"].astype(str).str.strip().str.upper()
    
    # Map quote grams & purity based on symbol
    res["quote_unit_grams"] = res["Symbol"].map(lambda s: CONTRACT_FACTS.get(s, {}).get("quote_unit_grams", 10))
    res["purity"] = res["Symbol"].map(lambda s: CONTRACT_FACTS.get(s, {}).get("purity", 999))
    
    purity_factor = TARGET_PURITY / res["purity"]
    
    for col in ["Close", "Open", "High", "Low"]:
        if col in res.columns:
            res[f"{col}_raw_per_g"] = res[col] / res["quote_unit_grams"]
            res[f"{col}_per_g_999"] = res[f"{col}_raw_per_g"] * purity_factor
            
    # Cleanup helper temp columns
    res = res.drop(columns=["quote_unit_grams", "purity"])
    return res
