import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = r'C:\Users\Junior T.I\.ssh\id_rsa'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

print("--- RESETTING INGESTION STATE ---")

# Truncate tables
tables = ["empresas", "estabelecimento", "socios"]
for table in tables:
    print(f"Truncating hemn_update_tmp.{table}...")
    client.exec_command(f'clickhouse-client --query "TRUNCATE TABLE hemn_update_tmp.{table}"')

# Reset log markers
log_file = "/var/www/hemn_cloud/ingest_march_2026.log"
patterns = ["Finished Empresas", "Finished Estabelecimentos", "Finished Socios"]
for p in patterns:
    print(f"Removing '{p}' from log...")
    client.exec_command(f'sed -i "/{p}/d" {log_file}')

print("Reset complete.")
client.close()
