import paramiko
import os
import time

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = os.path.expanduser('~/.ssh/id_rsa')

def verify_batch():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)
        sftp = client.open_sftp()
        
        # 1. Upload test file
        sftp.put('test_enrich.xlsx', '/var/www/hemn_cloud/static/uploads/test_enrich.xlsx')
        
        # 2. Trigger enrichment via direct method call in a script
        script_content = """
import sys
sys.path.append('/var/www/hemn_cloud')
from cloud_engine import CloudEngine
import os

engine = CloudEngine()
tid = engine.start_enrich('/var/www/hemn_cloud/static/uploads/test_enrich.xlsx', '/var/www/hemn_cloud/static/uploads', 'nome', 'cpf')

# Wait for completion
import time
for _ in range(30):
    status = engine.get_task_status(tid)
    if status['status'] == 'COMPLETED':
        print(f"DONE|{status['result_file']}")
        break
    elif status['status'] == 'FAILED':
        print(f"ERROR|{status['message']}")
        break
    time.sleep(1)
"""
        with sftp.open('/tmp/run_batch_test.py', 'w') as f:
            f.write(script_content)
            
        stdin, stdout, stderr = client.exec_command('/var/www/hemn_cloud/venv/bin/python3 /tmp/run_batch_test.py')
        out = stdout.read().decode()
        print(f"Result: {out}")
        
        if 'DONE|' in out:
            remote_result = out.split('|')[1].strip()
            sftp.get(remote_result, 'batch_result_verified.xlsx')
            print("Downloaded result to batch_result_verified.xlsx")
        
        sftp.close()

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    verify_batch()
