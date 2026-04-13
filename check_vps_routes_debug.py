import paramiko
import os

hostname = "129.121.45.136"
port = 22022
username = "root"
ssh_key_path = os.path.expanduser("~/.ssh/id_rsa")

def list_routes():
    key = paramiko.RSAKey.from_private_key_file(ssh_key_path)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, port=port, username=username, pkey=key)
    
    cmd = """
cd /var/www/hemn_cloud
python3 -c "
from HEMN_Cloud_Server import app
for route in app.routes:
    print(f'{route.methods} {route.path}')
"
"""
    stdin, stdout, stderr = client.exec_command(cmd)
    print("STDOUT:\n", stdout.read().decode())
    print("STDERR:\n", stderr.read().decode())
    client.close()

if __name__ == "__main__":
    list_routes()
