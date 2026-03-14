import sqlite3
import os

db_path = r'c:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\HEMN.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    users = conn.execute("SELECT username, role, password FROM users").fetchall()
    for user in users:
        print(f"User: {user['username']}, Role: {user['role']}, Pass: {user['password']}")
    conn.close()
else:
    print("Database not found")
