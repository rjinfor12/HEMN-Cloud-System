import sqlite3
import os

db_file = 'hemn_cloud_vps_migrating.db'
if not os.path.exists(db_file):
    print(f"File not found: {db_file}")
    exit(1)

conn = sqlite3.connect(db_file)
cur = conn.cursor()
try:
    cur.execute('SELECT username, password FROM users WHERE username = "admin" COLLATE NOCASE')
    row = cur.fetchone()
    if row:
        print(f"USER: {row[0]}")
        print(f"HASH_START: {row[1][:15]}")
    else:
        print("Admin user not found in this database.")
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()
