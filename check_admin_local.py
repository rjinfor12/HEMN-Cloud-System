import sqlite3
import os

DB_PATH = r'c:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\hemn_cloud.db'

def get_admin_data():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    user = conn.execute("SELECT * FROM users WHERE username='admin' COLLATE NOCASE").fetchone()
    if user:
        print(dict(user))
    else:
        print("Admin user not found in local DB.")
    conn.close()

if __name__ == "__main__":
    get_admin_data()
