from cloud_engine import CloudEngine
import os

engine = CloudEngine()
filters = {
    "uf": "SP",
    "situacao": "02",
    "sem_governo": True,
    "tipo_tel": "TODOS"
}

output_dir = "/var/www/hemn_cloud/results"
os.makedirs(output_dir, exist_ok=True)

print("Starting test extraction...")
tid = engine.start_extraction(filters, output_dir, username="test_user")
print(f"Task started: {tid}")

import time
for _ in range(30):
    status = engine.get_task_status(tid)
    print(f"Status: {status.get('status')} - {status.get('message')} - Progress: {status.get('progress')}%")
    if status.get('status') in ['COMPLETED', 'FAILED']:
        break
    time.sleep(2)

if status.get('status') == 'FAILED':
    print(f"ERROR: {status.get('message')}")
else:
    print("Extraction successful!")
