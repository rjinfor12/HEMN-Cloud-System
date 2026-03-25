import paramiko, os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

# Query para ver contagem de registros
queries = [
    "SELECT count() FROM hemn_update_tmp.empresas",
    "SELECT count() FROM hemn_update_tmp.estabelecimento",
    "SELECT count() FROM hemn_update_tmp.socios"
]

results = []
for q in queries:
    cmd = f'clickhouse-client -q "{q}"'
    stdin, stdout, stderr = client.exec_command(cmd)
    res = stdout.read().decode().strip()
    results.append(f"Q: {q} -> R: {res}")

print("\n".join(results))
client.close()
