import requests
import json
import time

API = "http://localhost:8000/areadocliente"
# Login might be needed, but I'll try to check /tasks/active if it's open or use the token from elsewhere if I can find it.
# Actually, I can just talk to the CloudEngine directly via a script to see if IT works.
from cloud_engine import CloudEngine
import os

engine = CloudEngine(db_path="hemn_cloud.db")
# Create a test task
tid = engine.start_extraction({"uf": "RJ", "cidade": "NITEROI"}, "storage/results", username="test_user")
print(f"Created task: {tid}")

# Check status in DB
import sqlite3
conn = sqlite3.connect("hemn_cloud.db")
conn.row_factory = sqlite3.Row
row = conn.execute("SELECT * FROM background_tasks WHERE id = ?", (tid,)).fetchone()
conn.close()

if row:
    print(f"DB Row - filters: {row['filters']}")
    if row['filters']:
        print("SUCCESS: Filters saved in DB.")
    else:
        print("FAILURE: Filters NOT saved in DB.")
else:
    print("Task not found in DB.")

# Test get_task_status
status = engine.get_task_status(tid)
print(f"Engine status response: {status.get('filters')}")
if status.get('filters'):
    print("SUCCESS: Filters returned by engine.")
else:
    print("FAILURE: Filters NOT returned by engine.")
