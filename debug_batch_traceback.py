import paramiko
import os
import time

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = os.path.expanduser('~/.ssh/id_rsa')

def run_debug():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)
        sftp = client.open_sftp()
        
        # runner with traceback
        runner_content = """
import sys
import traceback
sys.path.append('/var/www/hemn_cloud')
from cloud_engine import CloudEngine
import os
import time

try:
    engine = CloudEngine()
    # Mocking the _run_enrich steps to see where it fails
    # We'll run it synchronously for the test
    engine._run_enrich('DEBUG_TID', '/var/www/hemn_cloud/static/uploads/test_enrich.xlsx', '/var/www/hemn_cloud/static/uploads', 'nome', 'cpf')
    print("DONE|SUCCESS")
except Exception:
    print("TRACEBACK_START")
    traceback.print_exc()
    print("TRACEBACK_END")
"""
        with sftp.open('/tmp/debug_runner.py', 'w') as f:
            f.write(runner_content)
            
        stdin, stdout, stderr = client.exec_command('/var/www/hemn_cloud/venv/bin/python3 /tmp/debug_runner.py')
        out = stdout.read().decode()
        err = stderr.read().decode()
        print(f"STDOUT: {out}")
        print(f"STDERR: {err}")
            
        sftp.close()
    finally:
        client.close()

if __name__ == "__main__":
    run_debug()
