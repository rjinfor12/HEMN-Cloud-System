import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

file_path = '/var/www/hemn_cloud/static/admin_monitor.html'
stdin, stdout, stderr = client.exec_command(f'cat {file_path}')
content = stdout.read().decode('utf-8', errors='replace')
print(content)

client.close()
