import sqlite3
import os

DB_PATH = r'c:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\hemn_cloud.db'

def check_clinicas():
    if not os.path.exists(DB_PATH):
        print(f"DB not found at {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    users = conn.execute("SELECT username, role, valor_mensal, vencimento_dia FROM users WHERE role='CLINICAS'").fetchall()
    print(f"Found {len(users)} clinical users:")
    for u in users:
        print(dict(u))
    conn.close()

if __name__ == "__main__":
    check_clinicas()
