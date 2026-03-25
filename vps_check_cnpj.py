import paramiko, os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

# Comandos de auditoria SQL
# Queremos ver se existe a tabela empresas/estabelecimentos e a data_referencia
queries = [
    "SELECT COUNT(*) FROM estabelecimentos",
    "SELECT data_referencia FROM estabelecimentos LIMIT 1",
    "SELECT COUNT(*) FROM empresas",
    "SELECT data_referencia FROM empresas LIMIT 1",
    "SELECT COUNT(*) FROM socios"
]

results = []
for q in queries:
    cmd = f'sqlite3 /var/www/hemn_cloud/cnpj.db "{q};"'
    stdin, stdout, stderr = client.exec_command(cmd)
    res = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    results.append(f"Q: {q} -> R: {res} | E: {err}")

print("\n".join(results))
client.close()
