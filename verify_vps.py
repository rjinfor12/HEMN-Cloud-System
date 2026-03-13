import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

print("--- VPS FILE CHECK ---")
stdin, stdout, stderr = client.exec_command('ls -lh /var/www/hemn_cloud/')
print(stdout.read().decode())

stdin, stdout, stderr = client.exec_command('tail -n 10 /var/www/hemn_cloud/server_stdout.log')
print("STDOUT:", stdout.read().decode())

client.close()
