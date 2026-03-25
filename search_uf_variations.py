import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = r'C:\Users\Junior T.I\.ssh\id_rsa'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

print("--- SEARCHING FOR UF COLUMN VARIATIONS ---")
# Use single quotes for ClickHouse query, and double quotes for PowerShell wrapper if needed
query = "SELECT name, type FROM system.columns WHERE database = 'hemn' AND table = 'empresas' AND lower(name) = 'uf'"
stdin, stdout, stderr = client.exec_command(f'clickhouse-client --query "{query}"')
print(stdout.read().decode())
client.close()
