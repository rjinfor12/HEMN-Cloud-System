import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

print("--- STARTING INGESTION SCRIPT ON VPS ---")
# Use nohup to run in background
cmd = 'nohup python3 /var/www/hemn_cloud/vps_ingest_march_2026.py > /var/www/hemn_cloud/ingest_march_2026.log 2>&1 &'
client.exec_command(cmd)

print("Ingestion script started in background.")
print("Check log with: tail -f /var/www/hemn_cloud/ingest_march_2026.log")

client.close()
