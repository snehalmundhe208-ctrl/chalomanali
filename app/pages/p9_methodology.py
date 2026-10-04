"""
Page 9: Methodology, Assumptions & Glossary.
"""

import streamlit as st
from assets.theme import init_page_theme, render_hero_banner
from data.loader import get_or_load_dataset

def render():
    init_page_theme()
    _, _, is_synthetic = get_or_load_dataset()
    
    render_hero_banner(
        title="Methodology, Assumptions & Glossary",
        subtitle="Plain-English explanations, quantitative formulas, key trading assumptions, and system limitations",
        is_synthetic=is_synthetic
    )

    # 1. Methodology & Mathematical Formulas
    with st.container(border=True):
        st.markdown("### 🧮 Quantitative Normalization Mathematics")
        st.latex(r"\text{Price}_{\text{raw/g}} = \frac{\text{Quoted Price}}{\text{Quote Base Grams}}")
        st.latex(r"\text{Price}_{999/\text{g}} = \text{Price}_{\text{raw/g}} \times \left( \frac{999}{\text{Contract Purity}} \right)")
        st.markdown(
            "**Worked Conversion Factors:**\n"
            "- **GOLDM** (per 10g @ 995 purity): `(Price / 10) × (999 / 995) = Price × 0.10040201...`\n"
            "- **GOLDTEN** (per 10g @ 999 purity): `Price / 10 = Price × 0.10`\n"
            "- **GOLDGUINEA** (per 8g @ 999 purity): `Price / 8 = Price × 0.125`\n"
            "- **GOLDPETAL** (per 1g @ 999 purity): `Price / 1 = Price × 1.00`"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # 2. Key Trading Assumptions & Friction Model
    with st.container(border=True):
        st.markdown("### ⚙️ Key Trading Assumptions & Cost Friction Model")
        st.markdown(
            """
            1. **Transaction Cost Friction**:
               - **Brokerage**: Default 0.01% per trade leg (configurable).
               - **Exchange Fee**: ₹1.5 per ₹100,000 turnover (0.0015% per leg).
               - **CTT / Statutory Charges**: 0.01% on transaction turnover.
               - **Bid-Ask Slippage**: Default ₹0.50 per gram per leg execution impact.
            
            2. **Strict Walk-Forward Execution ($t \\to t+1$)**:
               - Signals are calculated at market close of day $t$ using only data up to $t$.
               - Trade entries and exits execute at the open/close of day $t+1$ to strictly eliminate look-ahead bias.
            
            3. **Liquidity Filter**:
               - Trades are suppressed on thin volume trading days (minimum 5 contracts traded, minimum 10 open interest).
            
            4. **Contract Expiry Handling**:
               - Contracts are tracked strictly by `ExpiryDate`. Continuous near-month stitching is prohibited to prevent artificial price gaps.
            """
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # 3. Demo Data Caveat Card
    with st.container(border=True):
        st.markdown("### ⚠️ Data Source & Synthetic Demo Caveat")
        st.markdown(
            """
            - **Synthetic Demo Data**: When live scraping of MCX Bhavcopy is unavailable, the application automatically falls back to a realistic synthetic gold futures generator (fixed seed 42 for 100% reproducibility).
            - **Demo Data Badging**: When running on synthetic data, every page displays the persistent **`DATA SOURCE: DEMO DATA (synthetic)`** badge, and backtest/verdict banners explicitly state **`(Result on DEMO data)`**. Synthetic data is never presented as real market data.
            """
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # 4. Glossary of Terms
    with st.container(border=True):
        st.markdown("### 📖 Glossary of Derivatives Terms")
        st.markdown(
            """
            - **MCX Daily Bhavcopy**: Official daily closing report published by Multi Commodity Exchange of India.
            - **Rolling Z-Score**: Number of standard deviations a pairwise spread strays from its 20-day moving average.
            - **Tender Period**: 5 business days prior to contract expiry during which open contracts enter physical delivery mode.
            - **Verdict Engine**: Rigorous classifier that outputs **'No persistent edge after costs'** when trading friction exceeds strategy gross returns.
            """
        )

if __name__ == "__main__":
    render()
