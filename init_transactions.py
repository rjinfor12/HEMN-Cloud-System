import sqlite3
import os

DB_PATH = "hemn_cloud.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create credit_transactions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS credit_transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        type TEXT NOT NULL, -- 'DEBIT', 'CREDIT'
        amount REAL NOT NULL,
        module TEXT,        -- 'MANUAL', 'EXTRACT', 'ENRICH', 'CARRIER', 'ADMIN'
        description TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (username) REFERENCES users (username)
    )
    """)
    
    # Ensure indexes for performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_username ON credit_transactions(username)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_timestamp ON credit_transactions(timestamp)")
    
    conn.commit()
    conn.close()
    print("Database initialized with credit_transactions table.")

if __name__ == "__main__":
    init_db()
