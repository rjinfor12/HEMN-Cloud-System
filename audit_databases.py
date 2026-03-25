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

print("--- TABLES IN 'hemn' ---")
print(run_ch("SHOW TABLES FROM hemn"))

print("\n--- TABLES IN 'hemn_update_tmp' ---")
print(run_ch("SHOW TABLES FROM hemn_update_tmp"))

print("\n--- DUPLICATE CHECK (municipio in tmp) ---")
print(f"Total count: {run_ch('SELECT count() FROM hemn_update_tmp.municipio')}")
print(f"Unique count: {run_ch('SELECT count(DISTINCT codigo) FROM hemn_update_tmp.municipio')}")

client.close()
