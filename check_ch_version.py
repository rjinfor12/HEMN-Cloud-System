import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

print("--- VERIFICANDO VERSÃO DA BASE NO CLICKHOUSE ---")
# Querying metadata table for db_version
cmd = 'clickhouse-client -q "SELECT value FROM hemn._metadata WHERE key = \'db_version\'"'
stdin, stdout, stderr = client.exec_command(cmd)
version = stdout.read().decode().strip()
print(f"VERSÃO ATUAL: {version}")

# Also checking record counts for sanity
cmd = 'clickhouse-client -q "SELECT count() FROM hemn.empresas"'
stdin, stdout, stderr = client.exec_command(cmd)
count = stdout.read().decode().strip()
print(f"TOTAL DE EMPRESAS: {count}")

client.close()
