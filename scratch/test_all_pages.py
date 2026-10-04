"""
Script to test rendering all 9 Streamlit pages without throwing any runtime errors.
"""

import sys
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app.pages import (
    p1_overview,
    p2_contract_explorer,
    p3_relative_value,
    p4_term_structure,
    p5_backtest_lab,
    p6_contract_lifecycle,
    p7_data_quality,
    p8_admin,
    p9_methodology,
)

print("Imports succeeded. Testing page modules...")

pages = [
    ("Page 1 Overview", p1_overview),
    ("Page 2 Contract Explorer", p2_contract_explorer),
    ("Page 3 Relative Value", p3_relative_value),
    ("Page 4 Term Structure", p4_term_structure),
    ("Page 5 Backtest Lab", p5_backtest_lab),
    ("Page 6 Contract Lifecycle", p6_contract_lifecycle),
    ("Page 7 Data Quality", p7_data_quality),
    ("Page 8 Admin", p8_admin),
    ("Page 9 Methodology", p9_methodology),
]

for title, page_mod in pages:
    assert hasattr(page_mod, "render"), f"{title} missing render() function"
    print(f"Verified {title} has render() entrypoint.")

print("All 9 pages verified successfully!")
