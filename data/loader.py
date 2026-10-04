"""
Data Loader for MCX Daily Bhavcopy Data.
Handles live scraping attempt, CSV upload ingestion, quality validation, SQLite caching,
and fallback to synthetic demo data generator.
"""

import pandas as pd
import numpy as np
import requests
import io
import os
from typing import Tuple, Dict, Any, Optional

from data.quality import validate_and_clean_bhavcopy
from data.cache import save_bhavcopy_to_cache, load_bhavcopy_from_cache, clear_cache
from data.synthetic import generate_synthetic_bhavcopy
from core.normalization import normalize_dataframe

def fetch_mcx_bhavcopy_live(date_str: str) -> pd.DataFrame:
    """
    Attempts to download MCX Bhavcopy CSV for a specific date (Format: DD/MM/YYYY or YYYY-MM-DD).
    MCX Bhavcopy public download URL endpoint structure.
    """
    try:
        # Standard MCX Bhavcopy URL format
        formatted_dt = pd.to_datetime(date_str).strftime("%d%m%Y")
        url = f"https://www.mcxindia.com/market-data/bhavcopy?Date={formatted_dt}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        }
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code == 200 and len(resp.content) > 500:
            # Parse CSV content
            df = pd.read_csv(io.BytesIO(resp.content))
            return df
    except Exception:
        pass
    return pd.DataFrame()

def load_data_from_csv_file(file_obj_or_path: Any) -> Tuple[pd.DataFrame, Dict[str, Any], bool]:
    """
    Loads raw MCX Bhavcopy CSV uploaded by user, validates quality, normalizes prices, and saves to cache.
    Returns (cleaned_and_normalized_df, quality_report, is_synthetic=False).
    """
    try:
        if isinstance(file_obj_or_path, str):
            df_raw = pd.read_csv(file_obj_or_path)
        else:
            df_raw = pd.read_csv(file_obj_or_path)
            
        df_clean, report = validate_and_clean_bhavcopy(df_raw)
        if not df_clean.empty:
            df_norm = normalize_dataframe(df_clean)
            # Save to SQLite cache as real (is_synthetic=False)
            save_bhavcopy_to_cache(df_norm, is_synthetic=False)
            return df_norm, report, False
    except Exception as e:
        pass
        
    return pd.DataFrame(), {}, False

def get_or_load_dataset(force_refresh: bool = False) -> Tuple[pd.DataFrame, Dict[str, Any], bool]:
    """
    Main entry point for retrieving dataset.
    Order of precedence:
    1. SQLite cache (if available and not force_refresh)
    2. Synthetic demo generator (if cache empty or live failed)
    
    Returns (normalized_df, quality_audit_report, is_synthetic).
    """
    if not force_refresh:
        df_cached, is_synth = load_bhavcopy_from_cache()
        if not df_cached.empty:
            df_clean, report = validate_and_clean_bhavcopy(df_cached)
            df_norm = normalize_dataframe(df_clean)
            return df_norm, report, is_synth
            
    # Fallback to Synthetic Demo Data Generator
    df_synth_raw = generate_synthetic_bhavcopy(start_date="2025-01-01", num_days=250, seed=42)
    df_synth_clean, report = validate_and_clean_bhavcopy(df_synth_raw)
    df_synth_norm = normalize_dataframe(df_synth_clean)
    
    # Save to cache as synthetic
    save_bhavcopy_to_cache(df_synth_norm, is_synthetic=True)
    return df_synth_norm, report, True
