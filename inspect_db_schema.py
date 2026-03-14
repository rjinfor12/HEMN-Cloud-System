import sqlite3
import os

db_path = 'hemn_cloud.db'
if not os.path.exists(db_path):
    print(f"Error: {db_path} not found")
else:
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT name, sql FROM sqlite_master WHERE type='table';")
    for name, sql in c.fetchall():
        print(f"--- Table: {name} ---")
        print(sql)
        print()
    conn.close()
