import paramiko

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = r'C:\Users\Junior T.I\.ssh\id_rsa'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)

python_script = """
import sys
import os
sys.path.insert(0, '/var/www/hemn_cloud')
import cloud_engine
print(f"File: {cloud_engine.__file__}")
from cloud_engine import CloudEngine
engine = CloudEngine()
print(f"Attributes: {dir(engine)}")
print(f"Has search_leads: {hasattr(engine, 'search_leads')}")
"""

sftp = client.open_sftp()
with sftp.file('/tmp/debug_import.py', 'w') as f:
    f.write(python_script)
sftp.close()

stdin, stdout, stderr = client.exec_command("/var/www/hemn_cloud/venv/bin/python /tmp/debug_import.py")
print(stdout.read().decode('utf-8'))
print(stderr.read().decode('utf-8'))
client.close()
