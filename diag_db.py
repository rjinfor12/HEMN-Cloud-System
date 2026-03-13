import sqlite3
import os

db_path = "hemn_cloud.db"
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(background_tasks)")
    columns = [info[1] for info in cursor.fetchall()]
    print(f"Columns in background_tasks: {columns}")
    
    # Check if filters column exists
    if 'filters' in columns:
        print("SUCCESS: 'filters' column exists.")
        # Check last 5 tasks
        cursor.execute("SELECT id, filters FROM background_tasks ORDER BY created_at DESC LIMIT 5")
        rows = cursor.fetchall()
        print("\nLast 5 tasks:")
        for r in rows:
            print(f"ID: {r[0]} | Filters: {r[1]}")
    else:
        print("FAILURE: 'filters' column is MISSING.")
    
    conn.close()
