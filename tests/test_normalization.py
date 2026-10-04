"""
Unit tests for contract price normalization to 999 purity per gram.
"""

import pytest
import pandas as pd
from core.normalization import normalize_price, normalize_dataframe

def test_worked_example_goldm():
    """
    Test case from prompt:
    GOLDM @ 72,000 per 10g (995 purity) gives 7,200 raw per g,
    and about 7,228.94 at 999 purity.
    """
    price_999 = normalize_price(72000.0, "GOLDM")
    expected = 72000.0 / 10.0 * (999.0 / 995.0)  # 7228.9447...
    assert pytest.approx(price_999, 0.01) == round(expected, 4)

def test_worked_example_goldten():
    """
    GOLDTEN @ 72,300 per 10g (999 purity) gives 7,230.00 per g.
    """
    price_999 = normalize_price(72300.0, "GOLDTEN")
    assert price_999 == 7230.0

def test_worked_example_goldguinea():
    """
    GOLDGUINEA @ 57,600 per 8g (999 purity) gives 7,200.00 per g.
    """
    price_999 = normalize_price(57600.0, "GOLDGUINEA")
    assert price_999 == 7200.0

def test_worked_example_goldpetal():
    """
    GOLDPETAL @ 7,200 per 1g (999 purity) gives 7,200.00 per g.
    """
    price_999 = normalize_price(7200.0, "GOLDPETAL")
    assert price_999 == 7200.0

def test_normalize_dataframe():
    """
    Verifies DataFrame normalization across multiple contracts.
    """
    df = pd.DataFrame([
        {"Symbol": "GOLDM ", "Close": 72000.0, "Open": 71800.0},
        {"Symbol": "GOLDTEN", "Close": 72300.0, "Open": 72100.0},
    ])
    res = normalize_dataframe(df)
    assert "Close_per_g_999" in res.columns
    assert pytest.approx(res.loc[0, "Close_per_g_999"], 0.01) == 7228.94
    assert res.loc[1, "Close_per_g_999"] == 7230.0
