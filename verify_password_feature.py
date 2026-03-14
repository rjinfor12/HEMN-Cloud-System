import requests, os

API_BASE = "https://www.hemnsystem.com.br/areadocliente"

# 1. Get token (assuming existing user 'admin' or similar, I'll need to know a password or check DB)
# For testing purpose, I'll just check if the endpoint responds correctly to invalid data
print("Testing invalid request (missing token)...")
res = requests.post(f"{API_BASE}/user/change-password", json={})
print(f"Status: {res.status_code}, Response: {res.text}")

# 2. Check if the index_vps.html has the new code
print("\nChecking UI code presence...")
import paramiko
host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

stdin, stdout, stderr = client.exec_command("grep 'openPasswordModal' /var/www/hemn_cloud/index_vps.html")
print("Grep output for openPasswordModal:")
print(stdout.read().decode())

client.close()
