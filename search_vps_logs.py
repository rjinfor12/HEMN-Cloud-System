import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

log_path = '/var/www/hemn_cloud/ingest_march_2026.log'

print(f"--- SEARCHING LOG: {log_path} ---")

# Check for Empresas
print("\nSearching for 'Empresas':")
cmd = f"grep 'Empresas' {log_path}"
stdin, stdout, stderr = client.exec_command(cmd)
print(stdout.read().decode())

# Check for Estabelecimentos
print("\nSearching for 'Estabelecimentos':")
cmd = f"grep 'Estabelecimentos' {log_path}"
stdin, stdout, stderr = client.exec_command(cmd)
print(stdout.read().decode())

# Check for ERROR
print("\nSearching for 'ERROR':")
cmd = f"grep 'ERROR' {log_path}"
stdin, stdout, stderr = client.exec_command(cmd)
print(stdout.read().decode())

client.close()
