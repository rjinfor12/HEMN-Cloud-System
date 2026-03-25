import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

print("--- SCHEMA CHECK: hemn.empresas ---")
cmd = 'clickhouse-client -q "DESCRIBE hemn.empresas"'
stdin, stdout, stderr = client.exec_command(cmd)
print(stdout.read().decode())

print("\n--- CREATE TABLE: hemn.empresas ---")
cmd = 'clickhouse-client -q "SHOW CREATE TABLE hemn.empresas"'
stdin, stdout, stderr = client.exec_command(cmd)
print(stdout.read().decode())

print("\n--- SCHEMA CHECK: hemn.estabelecimentos ---")
cmd = 'clickhouse-client -q "DESCRIBE TABLE hemn.estabelecimentos"'
stdin, stdout, stderr = client.exec_command(cmd)
print(stdout.read().decode())

client.close()
