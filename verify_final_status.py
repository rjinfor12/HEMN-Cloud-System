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

print("--- FINAL PRODUCTION STATUS (hemn) ---")
print(f"Database Version: {run_ch('SELECT value FROM hemn._metadata WHERE key=\"db_version\"')}")

tables = ["empresas", "estabelecimento", "socios", "simples", "municipio"]
for t in tables:
    count = run_ch(f"SELECT count() FROM hemn.{t}")
    print(f"{t}: {count}")

client.close()
