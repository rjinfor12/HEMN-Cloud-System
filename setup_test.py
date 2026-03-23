import sqlite3
import os

DB_PATH = r'c:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\hemn_cloud.db'

def setup_test():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE users SET role='CLINICAS', valor_mensal=1099.0, vencimento_dia=15 WHERE username='testuser'")
    conn.commit()
    user = conn.execute("SELECT password FROM users WHERE username='testuser'").fetchone()
    print(f"Updated 'testuser' to CLINICAS. Password: {user[0]}")
    conn.close()

if __name__ == "__main__":
    setup_test()
