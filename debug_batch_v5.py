import paramiko
import os

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = os.path.expanduser('~/.ssh/id_rsa')

def run_debug_v5():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)
        sftp = client.open_sftp()
        
        script = """
import sys
import os
sys.path.append('/var/www/hemn_cloud')
from cloud_engine import CloudEngine

engine = CloudEngine()
tid = 'DEBUG_V5'
input_p = '/var/www/hemn_cloud/static/uploads/test_enrich.xlsx'
output_d = '/var/www/hemn_cloud/static/uploads'
output_file = os.path.join(output_d, f'Enriquecido_{tid[:8]}.xlsx')

try:
    print(f"STARTING: {output_file}")
    engine._run_enrich(tid, input_p, output_d, 'nome', 'cpf')
    if os.path.exists(output_file):
        print(f"SUCCESS_FILE: {output_file}")
    else:
        print("FAIL_FILE: Not found in uploads.")
        # Search anywhere in /var/www/hemn_cloud
        for root, dirs, files in os.walk('/var/www/hemn_cloud'):
            for f in files:
                if 'Enriquecido' in f:
                    print(f"FOUND_ELSEWHERE: {os.path.join(root, f)}")
except Exception:
    import traceback
    traceback.print_exc()
"""
        with sftp.open('/tmp/debug_v5.py', 'w') as f:
            f.write(script)
            
        stdin, stdout, stderr = client.exec_command('/var/www/hemn_cloud/venv/bin/python3 /tmp/debug_v5.py')
        print(f"STDOUT:\n{stdout.read().decode()}")
        print(f"STDERR:\n{stderr.read().decode()}")
        sftp.close()
    finally:
        client.close()

if __name__ == "__main__":
    run_debug_v5()
