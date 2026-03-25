import paramiko, os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

def run(cmd):
    stdin, stdout, stderr = client.exec_command(cmd)
    stdout.channel.recv_exit_status()
    return stdout.read().decode('utf-8', errors='replace') + stderr.read().decode('utf-8', errors='replace')

print('=== 1. CONTAGEM DE LINHAS POR TABELA (hemn_update_tmp) ===')
# Query counts from system.parts for efficiency
query = "SELECT table, sum(rows) FROM system.parts WHERE database='hemn_update_tmp' AND active GROUP BY table"
r = run(f"clickhouse-client -q \"{query}\"")
print(r)

print('\n=== 2. STATUS DAS TAREFAS (background_tasks) ===')
db_path = "/var/www/hemn_cloud/hemn_cloud.db"
# Module might be lowercase or have different name
query = "SELECT id, module, status, progress, message, created_at FROM background_tasks WHERE created_at > '2026-03-25' ORDER BY created_at DESC LIMIT 10;"
r = run(f'sqlite3 {db_path} "{query}"')
print(r)

print('\n=== 3. ERROS NO LOG DE INGESTÃO (Estabelecimentos) ===')
log_path = "/var/www/hemn_cloud/ingest_march_2026.log"
r = run(f'grep "FAILED" {log_path}')
print(r)

print('\n=== 4. VERIFICANDO Empresas0.zip ===')
r = run(f'grep -C 5 "Empresas0.zip" {log_path}')
print(r)

client.close()
