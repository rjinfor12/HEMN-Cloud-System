import paramiko
import os

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = os.path.expanduser('~/.ssh/id_rsa')

def run_clean_debug():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)
        sftp = client.open_sftp()
        
        script = """
import sys
import traceback
import os
sys.path.append('/var/www/hemn_cloud')
from cloud_engine import CloudEngine

engine = CloudEngine()
try:
    print("Starting sync enrich...")
    engine._run_enrich('DEBUG_V4', '/var/www/hemn_cloud/static/uploads/test_enrich.xlsx', '/var/www/hemn_cloud/static/uploads', 'nome', 'cpf')
    print("Finished _run_enrich call.")
except Exception:
    print("CAUGHT EXCEPTION:")
    traceback.print_exc()
"""
        with sftp.open('/tmp/debug_v4.py', 'w') as f:
            f.write(script)
            
        stdin, stdout, stderr = client.exec_command('/var/www/hemn_cloud/venv/bin/python3 /tmp/debug_v4.py')
        print(f"STDOUT:\n{stdout.read().decode()}")
        print(f"STDERR:\n{stderr.read().decode()}")
        sftp.close()
    finally:
        client.close()

if __name__ == "__main__":
    run_clean_debug()
