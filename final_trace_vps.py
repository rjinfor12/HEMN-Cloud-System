import paramiko
import os

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = os.path.expanduser('~/.ssh/id_rsa')

def run_final_trace():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)
        sftp = client.open_sftp()
        
        script = """
import sys
import traceback
import os
import pandas as pd
from datetime import datetime

# Direct injection of the function logic to debug without importing the class
def debug_enrich():
    try:
        sys.path.append('/var/www/hemn_cloud')
        from cloud_engine import CloudEngine, remove_accents
        
        engine = CloudEngine()
        input_file = '/var/www/hemn_cloud/static/uploads/test_enrich.xlsx'
        output_dir = '/var/www/hemn_cloud/static/uploads'
        tid = 'FINAL_TRACE'
        
        # We'll just call the real method and let it fail
        print("Starting _run_enrich...")
        engine._run_enrich(tid, input_file, output_dir, 'nome', 'cpf')
        print("Method finished.")
        
    except Exception:
        print("CRITICAL_FAILURE_TRACEBACK:")
        traceback.print_exc()

if __name__ == "__main__":
    debug_enrich()
"""
        with sftp.open('/tmp/final_trace.py', 'w') as f:
            f.write(script)
            
        stdin, stdout, stderr = client.exec_command('/var/www/hemn_cloud/venv/bin/python3 /tmp/final_trace.py')
        print(f"STDOUT:\n{stdout.read().decode()}")
        print(f"STDERR:\n{stderr.read().decode()}")
        sftp.close()
    finally:
        client.close()

if __name__ == "__main__":
    run_final_trace()
