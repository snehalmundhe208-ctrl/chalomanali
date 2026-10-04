"""
SQLite Caching & Storage Layer for MCX Bhavcopy.
"""

import sqlite3
import pandas as pd
import os
from typing import Optional, Tuple

DB_FILE = "bhavcopy_cache.db"

def get_db_connection(db_path: str = DB_FILE) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS bhavcopy (
            Symbol TEXT,
            Date TEXT,
            ExpiryDate TEXT,
            Open REAL,
            High REAL,
            Low REAL,
            Close REAL,
            Volume INTEGER,
            OpenInterest INTEGER,
            is_synthetic INTEGER DEFAULT 0,
            PRIMARY KEY (Symbol, Date, ExpiryDate)
        )
    """)
    conn.commit()
    return conn

def save_bhavcopy_to_cache(df: pd.DataFrame, is_synthetic: bool = False, db_path: str = DB_FILE) -> int:
    """
    Saves or replaces Bhavcopy rows into SQLite cache.
    """
    if df.empty:
        return 0
        
    conn = get_db_connection(db_path)
    res = df.copy()
    res["is_synthetic"] = 1 if is_synthetic else 0
    
    # Required columns
    cols = ["Symbol", "Date", "ExpiryDate", "Open", "High", "Low", "Close", "Volume", "OpenInterest", "is_synthetic"]
    for c in cols:
        if c not in res.columns:
            res[c] = 0
            
    res = res[cols]
    
    # Save using replace / upsert
    res.to_sql("bhavcopy", conn, if_exists="append", index=False, method="multi")
    # De-duplicate
    conn.execute("""
        DELETE FROM bhavcopy WHERE rowid NOT IN (
            SELECT MAX(rowid) FROM bhavcopy GROUP BY Symbol, Date, ExpiryDate
        )
    """)
    conn.commit()
    count = len(res)
    conn.close()
    return count

def load_bhavcopy_from_cache(
    db_path: str = DB_FILE,
    symbol: Optional[str] = None
) -> Tuple[pd.DataFrame, bool]:
    """
    Loads Bhavcopy rows from SQLite.
    Returns (df, is_synthetic) tuple.
    """
    if not os.path.exists(db_path):
        return pd.DataFrame(), False
        
    conn = get_db_connection(db_path)
    
    query = "SELECT Symbol, Date, ExpiryDate, Open, High, Low, Close, Volume, OpenInterest, is_synthetic FROM bhavcopy"
    if symbol:
        query += f" WHERE Symbol = '{symbol}'"
        
    query += " ORDER BY Date ASC, ExpiryDate ASC"
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        return pd.DataFrame(), False
        
    is_synth = bool(df["is_synthetic"].iloc[0] == 1) if "is_synthetic" in df.columns else False
    return df, is_synth

def clear_cache(db_path: str = DB_FILE):
    """
    Clears SQLite database.
    """
    if os.path.exists(db_path):
        os.remove(db_path)
