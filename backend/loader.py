
import pandas as pd
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "chat_data.db")
DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "data-asistente.csv")

def load_data():
    """
    Loads data from SQLite database. 
    If DB doesn't exist, it tries to run ingestion from CSV.
    """
    if not os.path.exists(DB_PATH):
        if os.path.exists(DATA_PATH):
            print("Database not found. Running ingestion...")
            from .ingest import ingest_data
            ingest_data()
        else:
            raise FileNotFoundError(f"Database not found at {DB_PATH} and no CSV to ingest.")

    print(f"Loading data from SQLite: {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    try:
        # Load with rowid to preserve insertion order (which proxies for time)
        df = pd.read_sql("SELECT *, rowid FROM messages ORDER BY rowid", conn)
    finally:
        conn.close()

    # Post-load processing
    # SQLite stores dates as strings, so we MUST parse them back to datetime objects
    # for the temporal analysis to work.
    if 'fecha' in df.columns:
        df['fecha'] = pd.to_datetime(df['fecha'])

    # Ensure numeric columns are int and no NaNs
    numeric_cols = ['hora', 'input_tokens', 'output_tokens']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].fillna(0).astype(int)
    
    # Fill NaNs with empty string for text columns to match previous logic
    # (SQL might return None for NULLs)
    text_cols = ['text', 'intencion', 'product_type', 'product_detail', 'segment', 'sentiment', 'thread_id', 'type']
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].fillna("")

    # Final safety check: Replace any remaining NaNs (floats) with None
    # We must be careful not to convert datetime to object if possible, 
    # but for JSON serialization of other columns, we need to get rid of NaN.
    # Identify columns that have NaN
    # Note: timestamp columns with NaT are also problematic for some JSON encoders, 
    # but standard pandas to_dict usually handles them or we process them in main.py.
    
    # We already handled numeric_cols (int) and text_cols (str).
    # If there are other columns (e.g. floats), fill them with 0.0 or None.
    
    # Let's use `object` conversion ONLY for columns that are NOT fecha
    for col in df.columns:
        if col != 'fecha':
             # If column has NaN, replace with None
             if df[col].isnull().any():
                 df[col] = df[col].astype(object).where(pd.notnull(df[col]), None)


    print(f"Data loaded: {len(df)} records.")
    return df

# Singleton-like access to data (optional, or just load on startup)
_df_cache = None

def get_data():
    global _df_cache
    if _df_cache is None:
        _df_cache = load_data()
    return _df_cache
