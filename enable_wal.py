
import sqlite3
import os

DB_PATH = "/var/www/hemn_cloud/hemn_cloud.db"

def enable_wal():
    try:
        if not os.path.exists(DB_PATH):
            print(f"Error: Database not found at {DB_PATH}")
            return
            
        print(f"Opening database at {DB_PATH}")
        conn = sqlite3.connect(DB_PATH)
        curr = conn.execute("PRAGMA journal_mode")
        print(f"Current journal mode: {curr.fetchone()[0]}")
        
        print("Setting journal mode to WAL...")
        res = conn.execute("PRAGMA journal_mode=WAL")
        new_mode = res.fetchone()[0]
        print(f"New journal mode: {new_mode}")
        
        conn.close()
        print("Done.")
    except Exception as e:
        print(f"Failed to enable WAL: {str(e)}")

if __name__ == "__main__":
    enable_wal()
