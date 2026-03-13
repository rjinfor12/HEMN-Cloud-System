import sqlite3
import os

db_path = "hemn_cloud.db"
if not os.path.exists(db_path):
    print(f"Error: {db_path} does not exist.")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Tables: {tables}")
        for (table_name,) in tables:
            cursor.execute(f"PRAGMA table_info({table_name});")
            info = cursor.fetchall()
            print(f"Table {table_name}: {info}")
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"Count: {count}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()
