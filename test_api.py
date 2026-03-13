import requests
import time
import sys

base_url = "http://127.0.0.1:8000"
file_path = r"C:\Users\Junior T.I\OneDrive\Área de Trabalho\teta.xlsx"

print(f"Uploading {file_path}...")
with open(file_path, "rb") as f:
    files = {"file": f}
    # Forcing login auth token (simulating if we can/disabling auth if needed)
    # The endpoint uses `Depends(get_current_user)` which gets token from cookies.
    # To bypass auth easily, I'll login first.
    
    login_data = {"username": "admin", "password": "admin123"}
    session = requests.Session()
    resp = session.post(f"{base_url}/login", data=login_data)
    if resp.status_code != 200:
        print("Login failed:", resp.text)
        sys.exit(1)
        
    token = resp.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    upload_resp = session.post(f"{base_url}/upload", files=files, headers=headers)
    if upload_resp.status_code != 200:
        print("Upload failed:", upload_resp.text)
        sys.exit(1)
        
    file_id = upload_resp.json().get("file_id")
    print(f"Upload success. File ID: {file_id}")

print("Starting enrichment task...")
enrich_payload = {
    "file_id": file_id,
    "name_col": None,
    "cpf_col": None
}
task_resp = session.post(f"{base_url}/tasks/enrich", json=enrich_payload, headers=headers)
if task_resp.status_code != 200:
    print("Task start failed:", task_resp.text)
    sys.exit(1)

task_id = task_resp.json().get("task_id")
print(f"Task started. Task ID: {task_id}")

start_time = time.time()
while True:
    status_resp = session.get(f"{base_url}/tasks/{task_id}", headers=headers)
    data = status_resp.json()
    status = data.get("status")
    progress = data.get("progress")
    msg = data.get("message")
    
    elapsed = time.time() - start_time
    print(f"[{elapsed:.1f}s] Status: {status} | Progress: {progress}% | {msg}")
    
    if status in ["COMPLETED", "FAILED"]:
        print(f"\nFinal Result: {status}")
        print(f"Server Message: {msg}")
        break
        
    time.sleep(2)
