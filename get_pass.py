import sqlite3
import os

DB_PATH = r'c:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\hemn_cloud.db'

def get_junior_pass():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    user = conn.execute("SELECT password FROM users WHERE username='junior'").fetchone()
    if user:
        print(f"Password for junior: {user['password']}")
    else:
        print("User junior not found.")
    conn.close()

if __name__ == "__main__":
    get_junior_pass()
