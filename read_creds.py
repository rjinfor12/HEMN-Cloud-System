import sqlite3
import os

db_path = 'hemn_cloud.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    users = conn.execute("SELECT username, password FROM users LIMIT 5").fetchall()
    for user in users:
        print(f"User: {user['username']}, Pass: {user['password']}")
    conn.close()
else:
    print("Database not found")
