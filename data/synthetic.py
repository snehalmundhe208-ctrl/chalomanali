"""
Synthetic Data Generator for MCX Gold Futures Contracts.
Produces realistic 1+ year historical dataset with fixed random seed for reproducibility.
"""

import pandas as pd
import numpy as np
import datetime
from typing import Dict, List

def generate_synthetic_bhavcopy(
    start_date: str = "2025-01-01",
    num_days: int = 250,
    seed: int = 42
) -> pd.DataFrame:
    """
    Generates synthetic daily MCX Bhavcopy data for GOLDM, GOLDTEN, GOLDGUINEA, and GOLDPETAL.
    Uses fixed random seed so results and backtest verdicts are completely reproducible across runs.
    """
    np.random.seed(seed)
    
    dates = pd.bdate_range(start=start_date, periods=num_days).strftime("%Y-%m-%d").tolist()
    
    # Base gold spot price per gram at 999 purity (around ₹7,200 per gram)
    initial_spot_per_g = 7200.0
    
    # Geometric Brownian Motion for Spot Gold
    daily_returns = np.random.normal(loc=0.0003, scale=0.008, size=num_days)
    spot_prices = initial_spot_per_g * np.exp(np.cumsum(daily_returns))
    
    records = []
    
    # Contract specs
    # GOLDM: per 10g, 995 purity -> base price = spot * 10 * (995/999) = spot * 9.9599599...
    # GOLDTEN: per 10g, 999 purity -> base price = spot * 10
    # GOLDGUINEA: per 8g, 999 purity -> base price = spot * 8
    # GOLDPETAL: per 1g, 999 purity -> base price = spot * 1
    
    # Expiry monthly schedule (e.g. 5th of next month for GOLDM, 30th of next month for others)
    for i, date_str in enumerate(dates):
        current_dt = pd.to_datetime(date_str)
        spot_g = spot_prices[i]
        
        # Determine 2 active contract expiries per date (front and next month)
        # Expiry month 1: end of current month / early next month
        exp1_month = current_dt.month % 12 + 1
        exp1_year = current_dt.year + (1 if current_dt.month == 12 else 0)
        
        exp2_month = exp1_month % 12 + 1
        exp2_year = exp1_year + (1 if exp1_month == 12 else 0)
        
        # GOLDM Expiries (5th of expiry month)
        goldm_exp1 = f"{exp1_year}-{exp1_month:02d}-05"
        goldm_exp2 = f"{exp2_year}-{exp2_month:02d}-05"
        
        # Others Expiries (28th of expiry month)
        other_exp1 = f"{exp1_year}-{exp1_month:02d}-28"
        other_exp2 = f"{exp2_year}-{exp2_month:02d}-28"
        
        # Periodic noise / micro-mispricing spreads (simulating minor market inefficiency)
        sine_wave = np.sin(i / 8.0) * 4.5
        noise_m = np.random.normal(0, 2.0)
        noise_ten = np.random.normal(0, 2.5) + sine_wave
        noise_guinea = np.random.normal(0, 1.8) - sine_wave * 0.5
        noise_petal = np.random.normal(0, 0.4)
        
        # 1. GOLDM (quoted per 10g, 995 purity)
        raw_m_per_g = spot_g * (995.0 / 999.0)
        price_m = (raw_m_per_g * 10.0) + noise_m
        records.append({
            "Symbol": "GOLDM",
            "Date": date_str,
            "ExpiryDate": goldm_exp1,
            "Open": round(price_m * 0.998, 2),
            "High": round(price_m * 1.003, 2),
            "Low": round(price_m * 0.996, 2),
            "Close": round(price_m, 2),
            "Volume": int(np.random.randint(500, 3000)),
            "OpenInterest": int(np.random.randint(2000, 8000)),
        })
        
        # 2. GOLDTEN (quoted per 10g, 999 purity) - Only active from 2025-02-01 onwards
        if current_dt >= pd.to_datetime("2025-02-01"):
            price_ten = (spot_g * 10.0) + noise_ten
            records.append({
                "Symbol": "GOLDTEN",
                "Date": date_str,
                "ExpiryDate": other_exp1,
                "Open": round(price_ten * 0.997, 2),
                "High": round(price_ten * 1.004, 2),
                "Low": round(price_ten * 0.995, 2),
                "Close": round(price_ten, 2),
                "Volume": int(np.random.randint(100, 1200)),
                "OpenInterest": int(np.random.randint(500, 4000)),
            })
            
        # 3. GOLDGUINEA (quoted per 8g, 999 purity)
        price_guinea = (spot_g * 8.0) + noise_guinea
        records.append({
            "Symbol": "GOLDGUINEA",
            "Date": date_str,
            "ExpiryDate": other_exp1,
            "Open": round(price_guinea * 0.998, 2),
            "High": round(price_guinea * 1.002, 2),
            "Low": round(price_guinea * 0.997, 2),
            "Close": round(price_guinea, 2),
            "Volume": int(np.random.randint(50, 600)),
            "OpenInterest": int(np.random.randint(300, 2500)),
        })
        
        # 4. GOLDPETAL (quoted per 1g, 999 purity)
        price_petal = (spot_g * 1.0) + noise_petal
        records.append({
            "Symbol": "GOLDPETAL",
            "Date": date_str,
            "ExpiryDate": other_exp1,
            "Open": round(price_petal * 0.996, 2),
            "High": round(price_petal * 1.005, 2),
            "Low": round(price_petal * 0.994, 2),
            "Close": round(price_petal, 2),
            "Volume": int(np.random.randint(200, 2000)),
            "OpenInterest": int(np.random.randint(1000, 6000)),
        })
        
    df = pd.DataFrame(records)
    return df
