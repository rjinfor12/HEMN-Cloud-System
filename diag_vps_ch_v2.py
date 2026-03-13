import paramiko
import os
import sys

# Set output to UTF-8
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

print("--- VPS CLICKHOUSE CHECK ---")
stdin, stdout, stderr = client.exec_command('systemctl is-active clickhouse-server')
print("SERVICE STATUS:", stdout.read().decode().strip())

stdin, stdout, stderr = client.exec_command('tail -n 50 /var/www/hemn_cloud/server_error.log')
print("LATEST ERRORS:", stdout.read().decode())

client.close()
