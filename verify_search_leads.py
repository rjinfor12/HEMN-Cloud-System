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
from cloud_engine import CloudEngine
engine = CloudEngine()
res = engine.search_leads(search_type='NOME', search_term='ROGERIO ELIAS DO NASCIMENTO JUNIOR', scope='BRASIL')
import json
print(json.dumps(res, indent=2))
"""

sftp = client.open_sftp()
with sftp.file('/tmp/verify_search_leads.py', 'w') as f:
    f.write(python_script)
sftp.close()

stdin, stdout, stderr = client.exec_command("/var/www/hemn_cloud/venv/bin/python /tmp/verify_search_leads.py")
print(stdout.read().decode('utf-8'))
print(stderr.read().decode('utf-8'))
client.close()
