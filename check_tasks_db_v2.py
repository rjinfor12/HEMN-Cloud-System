import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

db_path = '/var/www/hemn_cloud/hemn_cloud.db'
cmd = f'sqlite3 {db_path} "SELECT id, module, status, progress, message, created_at FROM background_tasks ORDER BY created_at DESC LIMIT 10"'
stdin, stdout, stderr = client.exec_command(cmd)
print(stdout.read().decode())
print(stderr.read().decode())

client.close()
