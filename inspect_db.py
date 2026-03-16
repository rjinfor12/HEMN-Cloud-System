import sqlite3
import os

DB_PATH = "hemn_cloud.db"

if not os.path.exists(DB_PATH):
    print(f"Database not found at {DB_PATH}")
else:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    users = conn.execute("SELECT username, password, role, status FROM users").fetchall()
    print("--- User Records ---")
    for u in users:
        print(dict(u))
    conn.close()
