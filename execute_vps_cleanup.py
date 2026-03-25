import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

print("--- EXECUTING CLEANUP ---")

# 1. Delete db_chunks
print("Deleting /var/www/hemn_cloud/db_chunks...")
client.exec_command('rm -rf /var/www/hemn_cloud/db_chunks')

# 2. Drop hemn_update_tmp
print("Dropping ClickHouse database hemn_update_tmp...")
client.exec_command('clickhouse-client -q "DROP DATABASE IF EXISTS hemn_update_tmp"')

# 3. Clear storage (results and uploadsolder than 7 days)
print("Clearing old results and uploads...")
client.exec_command('find /var/www/hemn_cloud/storage/results -type f -mtime +7 -delete')
client.exec_command('find /var/www/hemn_cloud/storage/uploads -type f -mtime +7 -delete')

# 4. Final Space Check
print("\n--- FINAL SPACE CHECK ---")
stdin, stdout, stderr = client.exec_command('df -h /')
print(stdout.read().decode())

client.close()
