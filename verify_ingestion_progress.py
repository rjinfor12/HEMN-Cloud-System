import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = r'C:\Users\Junior T.I\.ssh\id_rsa'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

print("--- INGESTION PROGRESS ---")
stdin, stdout, stderr = client.exec_command('tail -n 10 /var/www/hemn_cloud/ingest_march_2026.log')
print(stdout.read().decode())

print("--- RECENT OUTPUT ---")
stdin, stdout, stderr = client.exec_command('tail -n 10 /var/www/hemn_cloud/ingest_output.log')
print(stdout.read().decode())

client.close()
