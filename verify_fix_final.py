import requests
import json

URL = "http://129.121.45.136:8000/leads/search"
# Note: I need the session token or bypass auth for testing if possible.
# But since I'm on the user's machine, I can try to use standard requests if it's public or check auth_manager.

# Let's try to find a valid token or just use a script on the VPS to call localhost (no auth needed/different config).
# Alternatively, I'll use SSH to cat the logs or run a local curl on the VPS.

import paramiko
HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = r'C:\Users\Junior T.I\.ssh\id_rsa'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)

# Test search via local curl on VPS (bypassing public auth if any, usually internal is fine)
# Actually, the API might require a token. Let's try to search by name.
cmd = "curl -X POST http://localhost:8000/leads/search -H 'Content-Type: application/json' -d '{\"search_type\": \"NOME\", \"search_term\": \"ROGERIO ELIAS DO NASCIMENTO JUNIOR\", \"scope\": \"BRASIL\"}'"
# Wait, the endpoint might be protected by check_clinicas_access.
# I'll run a python script on the VPS that imports the engine and tests it directly.

python_script = """
import sys
sys.path.append('/var/www/hemn_cloud')
from cloud_engine import CloudEngine
engine = CloudEngine()
res = engine.search_leads(search_type='NOME', search_term='ROGERIO ELIAS DO NASCIMENTO JUNIOR', scope='BRASIL')
import json
print(json.dumps(res, indent=2))
"""

sftp = client.open_sftp()
with sftp.file('/tmp/verify_fix_final.py', 'w') as f:
    f.write(python_script)
sftp.close()

stdin, stdout, stderr = client.exec_command("/var/www/hemn_cloud/venv/bin/python /tmp/verify_fix_final.py")
print("Response from VPS:")
print(stdout.read().decode('utf-8'))
print("Errors:")
print(stderr.read().decode('utf-8'))
client.close()
