import sqlite3
import os

DB_PATH = "hemn_cloud.db"

if os.path.exists(DB_PATH):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT username, role FROM users")
    rows = cursor.fetchall()
    print("USERS IN DATABASE:")
    for row in rows:
        print(f"User: {row[0]}, Role: {row[1]}")
    conn.close()
else:
    print(f"DB not found at {DB_PATH}")
