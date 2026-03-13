import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

print("--- VPS CLICKHOUSE CHECK ---")
stdin, stdout, stderr = client.exec_command('systemctl status clickhouse-server')
print("SERVICE STATUS:", stdout.read().decode())

stdin, stdout, stderr = client.exec_command('tail -n 50 /var/www/hemn_cloud/server_error.log')
print("LATEST ERRORS:", stdout.read().decode())

client.close()
