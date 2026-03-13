import requests
import time
import json

base_url = "http://localhost:8000"

import sqlite3

# 1. Login to get token
conn = sqlite3.connect('hemn_cloud.db')
user = conn.execute("SELECT username, password FROM users LIMIT 1").fetchone()
conn.close()

login_data = {"username": user[0], "password": user[1]} 
print(f"Logging in with {user[0]}...")
resp = requests.post(f"{base_url}/login", json=login_data)
if resp.status_code != 200:
    print(f"Login failed: {resp.text}")
    exit()

token = resp.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

# 2. Extract with VIVO only
print("Starting Extract (VIVO only)...")
extract_payload = {
    "uf": "SP",
    "cidade": "",
    "cnae": "",
    "tipo_tel": "CELULAR",
    "situacao": "02",
    "somente_com_telefone": True,
    "operadora_inc": "VIVO",
    "operadora_exc": "NENHUMA"
}
resp = requests.post(f"{base_url}/tasks/extract", json=extract_payload, headers=headers)
tid = resp.json().get("task_id")
print(f"Task started: {tid}")

# 3. Poll for status
while True:
    st = requests.get(f"{base_url}/tasks/status/{tid}", headers=headers).json()
    print(f"Progress: {st.get('progress')}% - {st.get('message')}")
    if st.get('status') in ['COMPLETED', 'FAILED']:
        print(st)
        break
    time.sleep(2)
