
import pandas as pd
import os
import sqlite3

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "data-asistente.csv")
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "chat_data.db")

def ingest_data():
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Data file not found at {DATA_PATH}")

    print("Loading data from CSV...")
    df = pd.read_csv(DATA_PATH, engine='python', on_bad_lines='skip')

    print("Cleaning data...")
    # Fix encoding in text columns
    text_columns = ['text', 'intencion', 'product_type', 'product_detail', 'segment']
    for col in text_columns:
        if col in df.columns:
            def clean_text(x):
                if pd.isna(x): return ""
                s = str(x).strip()
                if s.lower() == 'nan': return ""
                return s

            df[col] = df[col].apply(clean_text)

    # Normalize sentiment
    if 'sentiment' in df.columns:
        df['sentiment'] = df['sentiment'].replace({'negative': 'negativo'})
        df['sentiment'] = df['sentiment'].fillna('neutral')

    # Fill NaNs in critical columns
    fill_values = {
        'product_type': 'ninguno',
        'product_detail': 'ninguno',
        'intencion': 'sin intencion clara',
        'segment': 'desconocido'
    }
    df = df.fillna(fill_values)

    # Parse dates - crucial for SQLite storage
    if 'fecha' in df.columns:
        # First ensure datetime
        df['fecha'] = pd.to_datetime(df['fecha'], format='%Y-%m-%d', errors='coerce')
        # Store as string YYYY-MM-DD for consistency in SQLite
        # SQLite doesn't have a native date type, text is standard.
        df['fecha'] = df['fecha'].dt.strftime('%Y-%m-%d')

    # Ensure numeric columns
    numeric_cols = ['hora', 'input_tokens', 'output_tokens']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

    # Ensure thread_id is string
    if 'thread_id' in df.columns:
        df['thread_id'] = df['thread_id'].astype(str)

    # ---------------------------------------------------------
    # DEDUPLICATION
    # ---------------------------------------------------------
    initial_len = len(df)
    
    # 1. Deduplicate by ID if exists
    if 'id' in df.columns:
        print("Deduplicating by ID...")
        df = df.drop_duplicates(subset=['id'], keep='first')
        
    # 2. Secondary Deduplication by Content (Thread + Text + Time)
    # This handles cases where different IDs were generated for the same event
    print("Deduplicating by content (thread_id, text, type, fecha, hora)...")
    content_cols = [c for c in ['thread_id', 'text', 'type', 'fecha', 'hora'] if c in df.columns]
    if content_cols:
         df = df.drop_duplicates(subset=content_cols, keep='first')
    
    print(f"Removed {initial_len - len(df)} duplicate records total.")
    # ---------------------------------------------------------

    print(f"Persisting {len(df)} records to SQLite at {DB_PATH}...")
    
    conn = sqlite3.connect(DB_PATH)
    # Use replace to overwrite existing data for now
    df.to_sql('messages', conn, if_exists='replace', index=False)
    
    # Create indexes for performance
    cursor = conn.cursor()
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_thread_id ON messages (thread_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fecha ON messages (fecha)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_type ON messages (type)")
    conn.commit()
    conn.close()
    
    print("Ingestion complete.")

if __name__ == "__main__":
    ingest_data()
