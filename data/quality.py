"""
Data Quality Validation and Auditing Rules.
Enforces Section 4 quality checks on MCX Bhavcopy data.
"""

import pandas as pd
import numpy as np
import datetime
from typing import Dict, Any, Tuple

def validate_and_clean_bhavcopy(
    df: pd.DataFrame,
    requested_date_str: str = ""
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Validates, standardizes, and audits raw MCX Bhavcopy dataframe according to Section 4 rules.
    
    Returns:
      - Cleaned DataFrame
      - Quality Audit Report (dict of check results, counts of fixed/rejected rows)
    """
    audit_report = {
        "total_input_rows": len(df),
        "symbol_spaces_stripped_count": 0,
        "date_format_conversions": 0,
        "expiry_date_parsed_count": 0,
        "date_mismatch_flagged": False,
        "settlement_price_warning_count": 0,
        "thin_liquidity_rows_flagged": 0,
        "invalid_price_rows_rejected": 0,
        "clean_rows": 0,
        "rules_passed": {},
    }
    
    if df.empty:
        return df, audit_report
        
    res = df.copy()
    
    # 1. Clean Symbol column
    if "Symbol" in res.columns:
        original_symbols = res["Symbol"].astype(str)
        cleaned_symbols = original_symbols.str.strip().str.upper()
        audit_report["symbol_spaces_stripped_count"] = int((original_symbols != cleaned_symbols).sum())
        res["Symbol"] = cleaned_symbols
    else:
        audit_report["invalid_price_rows_rejected"] += len(res)
        return pd.DataFrame(), audit_report

    # Filter only relevant gold contracts
    valid_gold_symbols = ["GOLDM", "GOLDTEN", "GOLDGUINEA", "GOLDPETAL"]
    res = res[res["Symbol"].isin(valid_gold_symbols)].copy()

    # 2. Date parsing and validation
    # MCX responses use MM/DD/YYYY or YYYY-MM-DD or DD/MM/YYYY. We parse robustly to YYYY-MM-DD.
    if "Date" in res.columns:
        # Convert Date
        parsed_dates = pd.to_datetime(res["Date"], errors='coerce')
        audit_report["date_format_conversions"] = int(parsed_dates.notna().sum())
        res["Date"] = parsed_dates.dt.strftime("%Y-%m-%d")
    
    # Check requested date vs returned date validation rule
    if requested_date_str and not res.empty:
        returned_dates = res["Date"].unique()
        if len(returned_dates) > 0 and str(returned_dates[0]) != str(requested_date_str):
            audit_report["date_mismatch_flagged"] = True
            
    # 3. Compact ExpiryDate parsing (e.g., 04SEP2026, 05-OCT-2026, 2026-10-05)
    if "ExpiryDate" in res.columns:
        parsed_expiries = pd.to_datetime(res["ExpiryDate"], format='%d%b%Y', errors='coerce')
        # Fallback to general datetime parse if compact format parsing returns NaT
        mask_nat = parsed_expiries.isna()
        if mask_nat.any():
            parsed_expiries[mask_nat] = pd.to_datetime(res.loc[mask_nat, "ExpiryDate"], errors='coerce')
            
        res["ExpiryDate"] = parsed_expiries.dt.strftime("%Y-%m-%d")
        audit_report["expiry_date_parsed_count"] = int(parsed_expiries.notna().sum())
        
    # 4. Clean numeric columns & check non-negative prices
    numeric_cols = ["Open", "High", "Low", "Close", "Volume", "OpenInterest"]
    for col in numeric_cols:
        if col in res.columns:
            res[col] = pd.to_numeric(res[col], errors='coerce').fillna(0.0)
            
    # Reject rows with non-positive close prices
    valid_price_mask = res["Close"] > 0
    audit_report["invalid_price_rows_rejected"] += int((~valid_price_mask).sum())
    res = res[valid_price_mask].copy()

    # 5. Settlement / Close price warning flag for illiquid contracts (Volume < 10)
    thin_mask = res["Volume"] < 10
    audit_report["thin_liquidity_rows_flagged"] = int(thin_mask.sum())
    audit_report["settlement_price_warning_count"] = int(thin_mask.sum())
    res["is_illiquid"] = thin_mask

    audit_report["clean_rows"] = len(res)

    # Summarize rule evaluation
    audit_report["rules_passed"] = {
        "Rule 1 (Requested Date Match)": not audit_report["date_mismatch_flagged"],
        "Rule 2 (Date Standardized YYYY-MM-DD)": audit_report["date_format_conversions"] > 0,
        "Rule 3 (Symbol Whitespace Stripped)": True,
        "Rule 4 (Expiry Date Parsed)": audit_report["expiry_date_parsed_count"] > 0,
        "Rule 5 (Settlement Price Illiquidity Warning)": True,
        "Rule 6 (Track by Expiry Date)": "ExpiryDate" in res.columns,
    }

    return res, audit_report
