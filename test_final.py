import sys
import time
import threading
from cloud_engine import CloudEngine

# Create engine and test teta.xlsx
engine = CloudEngine(r"C:\HEMN_SYSTEM_DB\cnpj.db", r"C:\HEMN_SYSTEM_DB\hemn_carrier.db")
tid = engine.start_enrich(r"C:\Users\Junior T.I\OneDrive\Área de Trabalho\teta.xlsx", r"C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis", None, None)

# Fast monitor
start_time = time.time()
while True:
    status = engine.get_task_status(tid)
    elapsed = time.time() - start_time
    if status['status'] == 'PROCESSING':
        print(f"[{elapsed:.1f}s] {status['progress']}% | {status['message']}")
    if status['status'] in ('COMPLETED', 'FAILED'):
        print(f"\nFINAL: {status['status']} in {elapsed:.1f}s - Message: {status.get('message')}")
        break
    time.sleep(2)
