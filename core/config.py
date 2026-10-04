"""
Configuration & Hard-coded Contract Facts for MCX Gold Futures.
"""

from typing import Dict, Any

CONTRACT_FACTS: Dict[str, Dict[str, Any]] = {
    "GOLDM": {
        "name": "Gold Mini",
        "symbol": "GOLDM",
        "trading_unit_grams": 100,
        "quote_unit_grams": 10,
        "purity": 995,
        "expiry_window": "3rd to 5th of expiry month",
        "tender_period_days": 5,
        "description": "100g contract, quoted per 10g, 995 purity",
    },
    "GOLDTEN": {
        "name": "Gold Ten",
        "symbol": "GOLDTEN",
        "trading_unit_grams": 10,
        "quote_unit_grams": 10,
        "purity": 999,
        "expiry_window": "27th to 31st of expiry month",
        "tender_period_days": 5,
        "description": "10g contract, quoted per 10g, 999 purity (Listed 2025)",
        "start_year": 2025,
    },
    "GOLDGUINEA": {
        "name": "Gold Guinea",
        "symbol": "GOLDGUINEA",
        "trading_unit_grams": 8,
        "quote_unit_grams": 8,
        "purity": 999,
        "expiry_window": "27th to 31st of expiry month",
        "tender_period_days": 5,
        "description": "8g contract, quoted per 8g, 999 purity",
    },
    "GOLDPETAL": {
        "name": "Gold Petal",
        "symbol": "GOLDPETAL",
        "trading_unit_grams": 1,
        "quote_unit_grams": 1,
        "purity": 999,
        "expiry_window": "27th to 31st of expiry month",
        "tender_period_days": 5,
        "description": "1g contract, quoted per 1g, 999 purity",
    }
}

# Default trading cost assumptions (labeled as assumptions in UI)
DEFAULT_COSTS = {
    "brokerage_pct": 0.0001,      # 0.01% (Brokerage assumption)
    "exchange_fee_pct": 0.000015, # 0.0015% (MCX exchange fee assumption)
    "slippage_per_gram": 0.50,    # ₹0.50 per gram bid-ask spread & market impact
    "stt_ctt_pct": 0.0001,        # 0.01% CTT assumption
}

# Liquidity filter defaults
DEFAULT_LIQUIDITY_FILTER = {
    "min_volume": 5,             # Minimum daily contracts traded
    "min_open_interest": 10,     # Minimum open contracts
}

# Backtest default parameters
DEFAULT_BACKTEST_PARAMS = {
    "z_entry": 1.5,
    "z_exit": 0.2,
    "lookback_window": 20,
    "max_holding_days": 15,
}

# Target standard purity benchmark
TARGET_PURITY = 999
