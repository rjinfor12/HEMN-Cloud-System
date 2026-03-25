import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

print("--- RESETTING INGESTION STATE ---")

# 1. Kill ingestion script
client.exec_command('pkill -f vps_ingest_march_2026.py')
print("Killed background process.")

# 2. Drop temporary database
client.exec_command('clickhouse-client -q "DROP DATABASE IF EXISTS hemn_update_tmp"')
print("Dropped hemn_update_tmp.")

# 3. Clear downloads
client.exec_command('rm -rf /var/www/hemn_cloud/downloads/*')
print("Cleared downloads folder.")

# 4. Truncate log
client.exec_command('truncate -s 0 /var/www/hemn_cloud/ingest_march_2026.log')
print("Truncated log file.")

client.close()
