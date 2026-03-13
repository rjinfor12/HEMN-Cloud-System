import sqlite3
import pandas as pd
import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

def run(cmd):
    stdin, stdout, stderr = client.exec_command(cmd)
    stdout.channel.recv_exit_status()
    return stdout.read().decode('utf-8', errors='replace') + stderr.read().decode('utf-8', errors='replace')

print("=== CHECKING LAST BACKGROUND TASK ===")
q = "SELECT id, status, progress, result_file, module, created_at FROM background_tasks ORDER BY created_at DESC LIMIT 5;"
print(run(f'sqlite3 /var/www/hemn_cloud/hemn_cloud.db "{q}"'))

print("\n=== CHECKING SAMPLES FROM CLICKHOUSE (IF USED) OR SQLITE ===")
# Note: The extraction usually goes to ClickHouse and then gets exported.
# Let's see if we can find where the data is stored.

client.close()
