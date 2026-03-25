import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = r'C:\Users\Junior T.I\.ssh\id_rsa'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

print("--- FETCHING LAST FAILED QUERY WITH 'uf' ---")
query = "SELECT query, exception, event_time FROM system.query_log WHERE type != 'QueryStart' AND exception LIKE '%uf%' ORDER BY event_time DESC LIMIT 1"
stdin, stdout, stderr = client.exec_command(f'clickhouse-client --query "{query}"')
print(stdout.read().decode())
client.close()
