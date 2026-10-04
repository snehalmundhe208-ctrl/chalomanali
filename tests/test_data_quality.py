"""
Unit tests for data quality audit rules.
"""

import pytest
import pandas as pd
from data.quality import validate_and_clean_bhavcopy

def test_symbol_whitespace_stripping():
    df_raw = pd.DataFrame([
        {"Symbol": "GOLDM   ", "Date": "2025-01-05", "ExpiryDate": "05FEB2025", "Close": 72000.0, "Volume": 100, "OpenInterest": 500},
    ])
    df_clean, report = validate_and_clean_bhavcopy(df_raw)
    
    assert df_clean.iloc[0]["Symbol"] == "GOLDM"
    assert report["symbol_spaces_stripped_count"] == 1

def test_date_mismatch_validation():
    df_raw = pd.DataFrame([
        {"Symbol": "GOLDM", "Date": "2025-01-05", "ExpiryDate": "05FEB2025", "Close": 72000.0, "Volume": 100, "OpenInterest": 500},
    ])
    _, report = validate_and_clean_bhavcopy(df_raw, requested_date_str="2025-01-06")
    
    assert report["date_mismatch_flagged"] is True

def test_reject_invalid_prices():
    df_raw = pd.DataFrame([
        {"Symbol": "GOLDM", "Date": "2025-01-05", "ExpiryDate": "05FEB2025", "Close": -10.0, "Volume": 100, "OpenInterest": 500},
        {"Symbol": "GOLDTEN", "Date": "2025-01-05", "ExpiryDate": "28FEB2025", "Close": 72300.0, "Volume": 100, "OpenInterest": 500},
    ])
    df_clean, report = validate_and_clean_bhavcopy(df_raw)
    
    assert len(df_clean) == 1
    assert df_clean.iloc[0]["Symbol"] == "GOLDTEN"
    assert report["invalid_price_rows_rejected"] == 1
