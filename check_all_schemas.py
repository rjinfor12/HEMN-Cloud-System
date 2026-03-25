import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

print("--- TABLES IN 'hemn' DATABASE ---")
cmd = 'clickhouse-client -q "SHOW TABLES FROM hemn"'
stdin, stdout, stderr = client.exec_command(cmd)
tables = stdout.read().decode().splitlines()
print(tables)

for table in tables:
    print(f"\n--- SCHEMA FOR hemn.{table} ---")
    cmd = f'clickhouse-client -q "SHOW CREATE TABLE hemn.{table}"'
    stdin, stdout, stderr = client.exec_command(cmd)
    print(stdout.read().decode())

client.close()
