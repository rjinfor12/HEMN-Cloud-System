
import paramiko
import os

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = os.path.expanduser('~/.ssh/id_rsa')

def run_remote_python(script_content):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)
        # Create a temp script on VPS
        sftp = client.open_sftp()
        with sftp.open('/tmp/debug_carrier.py', 'w') as f:
            f.write(script_content)
        sftp.close()
        
        # Run it
        stdin, stdout, stderr = client.exec_command("cd /var/www/hemn_cloud && ./venv/bin/python /tmp/debug_carrier.py")
        print("STDOUT:", stdout.read().decode())
        print("STDERR:", stderr.read().decode())
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

script = """
import sys
import os
sys.path.append('/var/www/hemn_cloud')
from cloud_engine import CloudEngine

engine = CloudEngine()
status = engine.get_carrier_status()
print(status)
"""

if __name__ == "__main__":
    run_remote_python(script)
