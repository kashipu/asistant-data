import requests
import sqlite3
import os
import time

BASE_URL = "http://localhost:8000/api"
DB_PATH = "data/chat_data.db"

def verify_persistence():
    print("Verifying Persistence...")
    
    # 1. Check if tables exist
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    tables = []
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Tables in DB: {tables}")
    finally:
        conn.close()
        
    required = ['referrals', 'failures']
    missing = [t for t in required if t not in tables]
    
    if missing:
        print(f"❌ Missing tables: {missing}")
        # Trigger API to force compute (if lazy loaded) - but Engine inits on startup
        # We might need to restart backend? 
        # The backend reload should have triggered init.
    else:
        print("✅ Persistence tables found.")

def benchmark_monitor():
    print("\nBenchmarking APIs...")
    start = time.time()
    res = requests.get(f"{BASE_URL}/messages?limit=50")
    print(f"GET /messages (50 items): {time.time() - start:.4f}s")
    
    start = time.time()
    res = requests.get(f"{BASE_URL}/referrals?limit=50")
    print(f"GET /referrals (50 items): {time.time() - start:.4f}s")
    
    start = time.time()
    res = requests.get(f"{BASE_URL}/failures?limit=50")
    print(f"GET /failures (50 items): {time.time() - start:.4f}s")

if __name__ == "__main__":
    # Wait a bit for reload
    time.sleep(2)
    verify_persistence()
    benchmark_monitor()
