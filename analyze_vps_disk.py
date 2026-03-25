import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

print("--- VPS DISK USAGE ANALYSIS (Top 20) ---")
# Finding directories larger than 500MB
cmd = 'du -ah / --max-depth=2 | sort -rh | head -n 20'
stdin, stdout, stderr = client.exec_command(cmd)
print(stdout.read().decode())

print("\n--- CLICKHOUSE DATA SIZE ---")
cmd = 'du -sh /var/lib/clickhouse'
stdin, stdout, stderr = client.exec_command(cmd)
print(stdout.read().decode())

client.close()
