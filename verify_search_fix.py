import paramiko
import os

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = os.path.expanduser('~/.ssh/id_rsa')

def run_verification():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)
        
        script_content = """
import sys
sys.path.append('/var/www/hemn_cloud')
import pandas as pd
from cloud_engine import CloudEngine

engine = CloudEngine(db_cnpj='', db_carrier='') # Paths don't matter for deep_search as it uses ch_client

res = engine.deep_search("ROGERIO ELIAS DO NASCIMENTO JUNIOR", "09752279473")
print(f"--- RESULTS COUNT: {len(res)} ---")
print(res.to_json(orient='records', indent=2))
"""
        # Upload script
        sftp = client.open_sftp()
        with sftp.open('/tmp/verify_fix.py', 'w') as f:
            f.write(script_content)
        
        # Run script
        stdin, stdout, stderr = client.exec_command('python3 /tmp/verify_fix.py')
        out = stdout.read().decode()
        err = stderr.read().decode()
        
        print("STDOUT:")
        print(out)
        if err:
            print("STDERR:")
            print(err)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    run_verification()
