import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = r'C:\Users\Junior T.I\.ssh\id_rsa'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

print("--- DISK SPACE ---")
stdin, stdout, stderr = client.exec_command('df -h /')
print(stdout.read().decode())

print("--- TABLES IN hemn_update_tmp ---")
query = "SELECT name FROM system.tables WHERE database = 'hemn_update_tmp'"
stdin, stdout, stderr = client.exec_command(f'clickhouse-client --query "{query}"')
print(stdout.read().decode())
client.close()
