"""
Unit tests for cost model calculations.
"""

import pytest
from core.cost_model import calculate_roundtrip_cost_per_gram, apply_cost_to_trade

def test_cost_calculation():
    costs = calculate_roundtrip_cost_per_gram(7200.0)
    
    assert "brokerage_per_g" in costs
    assert "slippage_per_g" in costs
    assert "total_cost_per_g" in costs
    
    # Slippage component is ₹0.50 * 2 = ₹1.00 per gram roundtrip
    assert costs["slippage_per_g"] == 1.00
    assert costs["total_cost_per_g"] > 1.00

def test_apply_cost_to_trade():
    raw_pnl = 15.0  # ₹15 / gram raw gain
    net_pnl = apply_cost_to_trade(raw_pnl, 7200.0)
    
    assert net_pnl < raw_pnl
    assert net_pnl > 0.0
