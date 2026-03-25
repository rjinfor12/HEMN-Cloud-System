import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

print("--- CLICKHOUSE ROW COUNTS (hemn_update_tmp) ---")
# Query system.parts to see counts per table
cmd = "clickhouse-client -q \"SELECT table, sum(rows) FROM system.parts WHERE database = 'hemn_update_tmp' AND active GROUP BY table\""
stdin, stdout, stderr = client.exec_command(cmd)
print(stdout.read().decode())

client.close()
