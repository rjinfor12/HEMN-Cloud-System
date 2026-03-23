import sqlite3
import os

db_path = r"c:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\hemn_cloud.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables in database:")
for t in tables:
    print(t[0])
    cursor.execute(f"PRAGMA table_info({t[0]})")
    cols = cursor.fetchall()
    for col in cols:
        print(f"  {col}")

conn.close()
