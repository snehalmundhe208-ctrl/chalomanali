"""
Page 8: Admin Console & Parameter Settings.
"""

import streamlit as st
import os
import pandas as pd
from assets.theme import init_page_theme, render_hero_banner
from data.loader import get_or_load_dataset, load_data_from_csv_file
from data.cache import clear_cache

def render():
    init_page_theme()
    df, _, is_synthetic = get_or_load_dataset()
    
    render_hero_banner(
        title="Admin Console & Data Management",
        subtitle="Password-gated administration, parameters adjustment, database re-indexing, and CSV export",
        is_synthetic=is_synthetic
    )

    # Simple Password Gate
    admin_pass = os.environ.get("ADMIN_PASSWORD", "admin123")
    
    if "admin_authed" not in st.session_state:
        st.session_state["admin_authed"] = False

    if not st.session_state["admin_authed"]:
        with st.container(border=True):
            st.markdown("### 🔒 Prototype Admin Authentication")
            input_pass = st.text_input("Enter Admin Password", type="password")
            if st.button("Authenticate"):
                if input_pass == admin_pass:
                    st.session_state["admin_authed"] = True
                    st.success("Authenticated successfully!")
                    st.rerun()
                else:
                    st.error("Invalid admin password.")
        return

    # Authenticated Admin Panel
    st.success("Authenticated as Administrator.")
    
    # 1. CSV Upload Section
    with st.container(border=True):
        st.markdown("### 📤 Upload Real MCX Bhavcopy CSV File")
        st.markdown("Upload real MCX Bhavcopy CSV files to ingest and replace synthetic demo data in SQLite cache.")
        
        uploaded_file = st.file_uploader("Choose MCX Bhavcopy CSV", type=["csv"])
        if uploaded_file is not None:
            df_norm, report, is_synth = load_data_from_csv_file(uploaded_file)
            if not df_norm.empty:
                st.success(f"Successfully uploaded and ingested {len(df_norm)} rows into SQLite cache as REAL MCX data!")
                st.json(report)
            else:
                st.error("Failed to parse uploaded CSV. Ensure standard MCX Bhavcopy column headers.")

    # 2. Database Management
    st.markdown("<br>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("### 🗄️ Cache & Database Actions")
        col_db1, col_db2 = st.columns(2)
        with col_db1:
            if st.button("Re-index & Refresh Synthetic Data"):
                clear_cache()
                st.success("SQLite cache cleared and re-indexed!")
                st.rerun()
        with col_db2:
            if not df.empty:
                csv_bytes = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download Current Dataset (CSV)",
                    data=csv_bytes,
                    file_name="mcx_gold_futures_dataset.csv",
                    mime="text/csv"
                )

if __name__ == "__main__":
    render()
