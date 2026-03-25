import paramiko
import os
import sys

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = r'C:\Users\Junior T.I\.ssh\id_rsa'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

# This script will run on the VPS to check the ACTUAL engine output
vps_script = """
import sys
import os
import sqlite3
from datetime import datetime
import json

# Add app dir to path
sys.path.append('/var/www/hemn_cloud')
from cloud_engine import CloudEngine

engine = CloudEngine(db_path='/var/www/hemn_cloud/hemn_cloud.db')
stats = engine.get_internal_stats()

print("--- INTERNAL STATS FROM VPS ---")
print(json.dumps(stats, indent=2))
"""

def run_vps_python(py_code):
    print(f"\n--- RUNNING REMOTE PYTHON SCRIPT ---")
    # Escape quotes for shell
    escaped_code = py_code.replace('"', '\\"').replace('$', '\\$')
    stdin, stdout, stderr = client.exec_command(f'python3 -c "{escaped_code}"')
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    if out: print(f"STDOUT:\n{out}")
    if err: print(f"STDERR:\n{err}")
    return out, err

run_vps_python(vps_script)

client.close()
