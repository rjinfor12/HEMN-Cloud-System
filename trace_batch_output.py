import paramiko
import os
import time

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = os.path.expanduser('~/.ssh/id_rsa')

def run_trace():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)
        sftp = client.open_sftp()
        
        trace_script = """
import sys
import os
sys.path.append('/var/www/hemn_cloud')
from cloud_engine import CloudEngine

engine = CloudEngine()
print(f"CWD: {os.getcwd()}")
input_p = '/var/www/hemn_cloud/static/uploads/test_enrich.xlsx'
output_d = '/var/www/hemn_cloud/static/uploads'

# Run synchronous
engine._run_enrich('TRACE_TID', input_p, output_d, 'nome', 'cpf')

for f in os.listdir(output_d):
    if 'Enriquecido' in f:
        print(f"FOUND|{os.path.join(output_d, f)}")
"""
        with sftp.open('/tmp/trace_runner.py', 'w') as f:
            f.write(trace_script)
            
        stdin, stdout, stderr = client.exec_command('/var/www/hemn_cloud/venv/bin/python3 /tmp/trace_runner.py')
        out = stdout.read().decode()
        print(f"OUTPUT:\n{out}")
        
        if 'FOUND|' in out:
            path = out.split('FOUND|')[1].strip()
            sftp.get(path, 'batch_result_trace.xlsx')
            print("Downloaded batch_result_trace.xlsx")
            
        sftp.close()
    finally:
        client.close()

if __name__ == "__main__":
    run_trace()
