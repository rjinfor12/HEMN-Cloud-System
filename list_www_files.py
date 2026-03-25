import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

print("--- FILES IN /var/www/hemn_cloud ---")
cmd = 'du -ah /var/www/hemn_cloud | sort -rh | head -n 20'
stdin, stdout, stderr = client.exec_command(cmd)
print(stdout.read().decode())

client.close()
