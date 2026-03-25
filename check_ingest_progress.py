import paramiko
import os
import time

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

print("--- INGESTION LOG (LAST 20 LINES) ---")
cmd = 'tail -n 20 /var/www/hemn_cloud/ingest_march_2026.log'
stdin, stdout, stderr = client.exec_command(cmd)
print(stdout.read().decode())

print("\n--- DATABASE STATUS ---")
cmd = 'clickhouse-client -q "SELECT table, count() FROM system.parts WHERE database = \'hemn_update_tmp\' GROUP BY table"'
stdin, stdout, stderr = client.exec_command(cmd)
print(stdout.read().decode())

client.close()
