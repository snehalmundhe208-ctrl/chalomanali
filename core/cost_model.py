"""
Trading Cost & Friction Model.
Calculates brokerage, exchange fees, taxes (CTT), and market slippage per gram.
"""

from typing import Dict, Any, Optional
from core.config import DEFAULT_COSTS

def calculate_roundtrip_cost_per_gram(
    price_per_g: float,
    custom_costs: Optional[Dict[str, float]] = None
) -> Dict[str, float]:
    """
    Calculates roundtrip transaction cost per gram for entering and exiting a trade.
    
    Components:
    1. Brokerage (2 legs: buy + sell)
    2. Exchange fee (2 legs: buy + sell)
    3. Slippage (2 legs: buy + sell)
    4. CTT / Taxes (2 legs)
    """
    costs = DEFAULT_COSTS.copy()
    if custom_costs:
        costs.update(custom_costs)
        
    brokerage_pct = costs.get("brokerage_pct", 0.0001)
    exchange_fee_pct = costs.get("exchange_fee_pct", 0.000015)
    slippage_per_g = costs.get("slippage_per_gram", 0.50)
    stt_ctt_pct = costs.get("stt_ctt_pct", 0.0001)
    
    # 2 legs for roundtrip
    brokerage = price_per_g * brokerage_pct * 2.0
    exchange_fee = price_per_g * exchange_fee_pct * 2.0
    slippage = slippage_per_g * 2.0
    ctt = price_per_g * stt_ctt_pct * 2.0
    
    total_cost_per_g = brokerage + exchange_fee + slippage + ctt
    
    return {
        "brokerage_per_g": round(brokerage, 4),
        "exchange_fee_per_g": round(exchange_fee, 4),
        "slippage_per_g": round(slippage, 4),
        "ctt_per_g": round(ctt, 4),
        "total_cost_per_g": round(total_cost_per_g, 4),
    }

def apply_cost_to_trade(
    pnl_raw_per_g: float,
    entry_price_per_g: float,
    custom_costs: Optional[Dict[str, float]] = None
) -> float:
    """
    Subtracts total roundtrip transaction costs from raw per-gram PnL.
    """
    cost_dict = calculate_roundtrip_cost_per_gram(entry_price_per_g, custom_costs)
    net_pnl_per_g = pnl_raw_per_g - cost_dict["total_cost_per_g"]
    return round(net_pnl_per_g, 4)
