import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

print("--- VPS TASK DATABASE CHECK ---")
stdin, stdout, stderr = client.exec_command('sqlite3 /var/www/hemn_cloud/hemn_cloud.db "SELECT id, status, progress, message FROM background_tasks ORDER BY created_at DESC LIMIT 5;"')
print(stdout.read().decode())

client.close()
