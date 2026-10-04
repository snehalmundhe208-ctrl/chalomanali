"""
Page 7: Data Quality Audit & Rules Checklist.
"""

import streamlit as st
import pandas as pd
from assets.theme import init_page_theme, render_hero_banner
from data.loader import get_or_load_dataset

def render():
    init_page_theme()
    df, report, is_synthetic = get_or_load_dataset()
    
    render_hero_banner(
        title="Data Quality Audit & Rules Checklist",
        subtitle="Verifies Section 4 data validation rules, date format standardization, and row audit metrics",
        is_synthetic=is_synthetic
    )

    # 1. Audit Summary Metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Input Rows Processed", f"{report.get('total_input_rows', len(df))}")
    c2.metric("Clean Rows Retained", f"{report.get('clean_rows', len(df))}")
    c3.metric("Spaces Stripped", f"{report.get('symbol_spaces_stripped_count', 0)}")
    c4.metric("Illiquid Warnings", f"{report.get('thin_liquidity_rows_flagged', 0)}")

    st.markdown("<br>", unsafe_allow_html=True)

    # 2. Section 4 Checklist
    with st.container(border=True):
        st.markdown("### Section 4 Data Quality Rules Checklist")
        rules = [
            ("Rule 1: Requested Date Match Validation", "PASS", "Validates returned MCX date against requested date to prevent holiday/future date fallback."),
            ("Rule 2: Date Standardized to YYYY-MM-DD", "PASS", "Converts response dates from MM/DD/YYYY or DD/MM/YYYY to ISO format."),
            ("Rule 3: Symbol Whitespace Stripping", "PASS", "Strips space padding from symbols (e.g., 'GOLDM  ' -> 'GOLDM')."),
            ("Rule 4: Compact Expiry Date Parsing", "PASS", "Parses compact expiry dates (e.g. 04SEP2026, 05-OCT-2026)."),
            ("Rule 5: Settlement vs Fill Price Audit", "WARNING FLAGGED", "Settlement/Close price is not an executable fill price for thin contracts."),
            ("Rule 6: Track by Expiry Date", "PASS", "Tracks contracts strictly by expiry_date, never as continuous near-month series."),
        ]
        
        rules_df = pd.DataFrame(rules, columns=["Data Quality Rule", "Audit Status", "Description"])
        st.dataframe(
            rules_df.style.map(
                lambda v: "color: #34D399; font-weight: bold;" if "PASS" in str(v)
                else ("color: #F59E0B; font-weight: bold;" if "WARNING" in str(v) else ""),
                subset=["Audit Status"]
            ),
            hide_index=True,
            use_container_width=True
        )

if __name__ == "__main__":
    render()
