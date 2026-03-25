import paramiko

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = r'C:\Users\Junior T.I\.ssh\id_rsa'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("--- Service Status ---")
stdin, stdout, stderr = client.exec_command("systemctl status hemn_cloud")
print(stdout.read().decode('utf-8', errors='replace'))

print("--- Nginx Status ---")
stdin, stdout, stderr = client.exec_command("systemctl status nginx")
print(stdout.read().decode('utf-8', errors='replace'))

print("--- Application Log (last 20 lines) ---")
stdin, stdout, stderr = client.exec_command("journalctl -u hemn_cloud -n 20 --no-pager")
print(stdout.read().decode('utf-8', errors='replace'))

client.close()
