import sqlite3
import os

db_path = "hemn_cloud.db"
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
else:
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(background_tasks)")
        columns = [info[1] for info in cursor.fetchall()]
        if 'filters' not in columns:
            print("[MIGRATION] Adicionando coluna 'filters' em background_tasks")
            conn.execute("ALTER TABLE background_tasks ADD COLUMN filters TEXT")
            conn.commit()
            print("MIGRATION SUCCESSFUL")
        else:
            print("COLUMN ALREADY EXISTS")
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        conn.close()
