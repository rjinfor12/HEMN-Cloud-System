import sqlite3
import json
from datetime import datetime

def check():
    conn = sqlite3.connect('/var/www/hemn_cloud/hemn_cloud.db')
    conn.row_factory = sqlite3.Row
    
    users = ["Vt", "admin"]
    for uname in users:
        user = conn.execute("SELECT * FROM users WHERE username = ?", (uname,)).fetchone()
        if user:
            print(f"\n--- USER DATA: {uname} ---")
            print(json.dumps(dict(user), indent=2))
        else:
            print(f"\nUser '{uname}' not found")
            
    print("\n--- TOP DEBIT TRANSACTIONS TODAY (ALL USERS) ---")
    today = datetime.now().strftime('%Y-%m-%d')
    txs = conn.execute("""
        SELECT username, amount, description, timestamp 
        FROM credit_transactions 
        WHERE type = 'DEBIT' AND date(timestamp) = ?
        ORDER BY amount DESC LIMIT 10
    """, (today,)).fetchall()
    for tx in txs:
        print(dict(tx))

    print("\n--- TOTAL DEBITS PER USER TODAY ---")
    summaries = conn.execute("""
        SELECT username, SUM(amount) as total 
        FROM credit_transactions 
        WHERE type = 'DEBIT' AND date(timestamp) = ?
        GROUP BY username
        ORDER BY total DESC
    """, (today,)).fetchall()
    for s in summaries:
        print(dict(s))
        
    conn.close()

if __name__ == "__main__":
    check()
