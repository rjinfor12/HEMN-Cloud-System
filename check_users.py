import sqlite3
import os

db_path = r"c:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\hemn_cloud.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT username, role FROM users")
    rows = cursor.fetchall()
    for row in rows:
        print(f"User: {row[0]}, Role: {row[1]}")
    conn.close()
else:
    print("Database not found")
