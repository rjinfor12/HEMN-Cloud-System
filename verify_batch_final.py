import paramiko
import os
import time

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = os.path.expanduser('~/.ssh/id_rsa')

def run_test():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)
        sftp = client.open_sftp()
        
        # 1. Upload test file
        sftp.put('test_enrich.xlsx', '/var/www/hemn_cloud/static/uploads/test_enrich.xlsx')
        
        # 2. Upload runner script
        runner_content = """
import sys
sys.path.append('/var/www/hemn_cloud')
from cloud_engine import CloudEngine
import os
import time

engine = CloudEngine()
tid = engine.start_enrich('/var/www/hemn_cloud/static/uploads/test_enrich.xlsx', '/var/www/hemn_cloud/static/uploads', 'nome', 'cpf')

for _ in range(60):
    status = engine.get_task_status(tid)
    if status['status'] == 'COMPLETED':
        print(f"DONE|{status['result_file']}")
        break
    elif status['status'] == 'FAILED':
        print(f"ERROR|{status['message']}")
        break
    time.sleep(1)
"""
        with sftp.open('/tmp/runner.py', 'w') as f:
            f.write(runner_content)
            
        # 3. Execute
        stdin, stdout, stderr = client.exec_command('/var/www/hemn_cloud/venv/bin/python3 /tmp/runner.py')
        out = stdout.read().decode().strip()
        print(f"Execution Output: {out}")
        
        if 'DONE|' in out:
            remote_path = out.split('|')[1]
            sftp.get(remote_path, 'batch_result_final.xlsx')
            print("Downloaded batch_result_final.xlsx")
            
        sftp.close()
    finally:
        client.close()

if __name__ == "__main__":
    run_test()
