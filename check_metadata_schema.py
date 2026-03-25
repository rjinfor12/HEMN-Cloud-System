import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

def run_ch(query):
    cmd = f'clickhouse-client -q "{query}"'
    stdin, stdout, stderr = client.exec_command(cmd)
    return stdout.read().decode().strip()

print("--- hemn._metadata (SCHEMA) ---")
try:
    print(run_ch("SHOW CREATE TABLE hemn._metadata"))
except:
    print("Table hemn._metadata not found or error")

print("\n--- hemn._metadata (COLUMNS) ---")
try:
    print(run_ch("DESCRIBE TABLE hemn._metadata"))
except:
    print("Error describing table")

client.close()
