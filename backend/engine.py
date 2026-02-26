
import pandas as pd
import sqlite3
import os
import time
from .loader import load_data, DB_PATH
from .referrals import detect_referrals
from .failures import detect_failures

class DataEngine:
    _instance = None

    def __init__(self):
        if DataEngine._instance is not None:
            raise Exception("This class is a singleton!")
        else:
            DataEngine._instance = self
            self.df = None
            self.referrals_df = None
            self.failures_df = None
            
            # Caches
            self.thread_lengths = None
            self.servilinea_threads = set()
            self.empty_msg_threads = set()
            
            self._initialize()

    @staticmethod
    def get_instance():
        if DataEngine._instance is None:
            DataEngine()
        return DataEngine._instance

    def _initialize(self):
        print("initializing Data Engine...")
        start_time = time.time()
        
        # 1. Load Core Data
        self.df = load_data()
        
        # 2. Pre-compute Thread Metadata (In-Memory)
        self.thread_lengths = self.df.groupby('thread_id').size()
        
        # Empty messages check
        self.empty_msg_threads = set(self.df[self.df['text'].str.strip() == '']['thread_id'].unique())
        
        # 3. Load or Compute Derived Analysis (Persisted)
        self._load_or_compute_referrals()
        self._load_or_compute_failures()
        
        print(f"Data Engine initialized in {time.time() - start_time:.2f}s")
    
    def _get_db_conn(self):
        return sqlite3.connect(DB_PATH)

    def _load_or_compute_referrals(self):
        conn = self._get_db_conn()
        try:
            print("Loading referrals from DB...")
            self.referrals_df = pd.read_sql("SELECT * FROM referrals", conn)
            # Quick validation: checking if referrals match current data version could be complex
            # For now, we assume if table exists, it's valid. 
            # In prod, we'd check a version hash.
            if self.referrals_df.empty and not self.df.empty:
                 raise Exception("Empty referrals table") # Force re-compute
        except Exception:
            print("Referrals not found or empty in DB. Computing...")
            self.referrals_df = detect_referrals(self.df)
            if not self.referrals_df.empty:
                self.referrals_df.to_sql('referrals', conn, if_exists='replace', index=False)
                # Index
                conn.execute("CREATE INDEX IF NOT EXISTS idx_ref_thread_id ON referrals (thread_id)")
                conn.commit()
        finally:
            conn.close()
            
        # Cache Servilinea Threads Set
        if not self.referrals_df.empty:
            self.servilinea_threads = set(self.referrals_df['thread_id'].unique())

    def _load_or_compute_failures(self):
        conn = self._get_db_conn()
        try:
            print("Loading failures from DB...")
            self.failures_df = pd.read_sql("SELECT * FROM failures", conn)
            if self.failures_df.empty and not self.df.empty:
                 raise Exception("Empty failures table")
        except Exception:
            print("Failures not found in DB. Computing...")
            self.failures_df = detect_failures(self.df)
            if not self.failures_df.empty:
                # Convert list/dict columns if any (failures usually flat)
                self.failures_df.to_sql('failures', conn, if_exists='replace', index=False)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_fail_thread_id ON failures (thread_id)")
                conn.commit()
        finally:
            conn.close()

    def get_messages(self, start_date=None, end_date=None):
        df_filtered = self.df
        if (start_date or end_date) and not df_filtered.empty and 'fecha' in df_filtered.columns:
            mask = pd.Series(True, index=df_filtered.index)
            if start_date:
                mask &= (df_filtered['fecha'] >= pd.to_datetime(start_date))
            if end_date:
                mask &= (df_filtered['fecha'] <= pd.to_datetime(end_date))
            df_filtered = df_filtered[mask]
        return df_filtered

    def get_referrals(self):
        return self.referrals_df

    def get_failures(self):
        return self.failures_df

    def get_thread_length(self, thread_id):
        return self.thread_lengths.get(thread_id, 0)
    
    def is_servilinea(self, thread_id):
        return thread_id in self.servilinea_threads

    def has_empty_messages(self, thread_id):
        return thread_id in self.empty_msg_threads

    def reload(self):
        print("Reloading Data Engine...")
        self.df = None
        self.referrals_df = None
        self.failures_df = None
        self.thread_lengths = None
        self.servilinea_threads = set()
        self.empty_msg_threads = set()
        self._initialize()

    def update_message(self, message_id: str, updates: dict):
        if self.df is not None and not self.df.empty:
            if 'id' in self.df.columns:
                mask = self.df['id'] == message_id
                if mask.any():
                    for k, v in updates.items():
                        if k in self.df.columns:
                            self.df.loc[mask, k] = v
            else:
                print("Warning: 'id' column not found in DataEngine dataframe")
