import sqlite3
import os

db_path = "/var/www/hemn_cloud/hemn_cloud.db"
if not os.path.exists(db_path):
    print("DB not found")
else:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    # Search for the task by the prefix c2e070
    tasks = conn.execute("SELECT id, module, status, progress, message, created_at FROM background_tasks WHERE id LIKE 'c2e070%'").fetchall()
    print("--- SEARCH RESULTS ---")
    if not tasks:
        print("No task found with ID prefix c2e070")
    for t in tasks:
        print(f"ID: {t['id']} | MOD: {t['module']} | STATUS: {t['status']} | PROG: {t['progress']}% | MSG: {t['message']}")
    conn.close()
