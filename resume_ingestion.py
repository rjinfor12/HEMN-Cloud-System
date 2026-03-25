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
    return stdout.read().decode('utf-8', errors='ignore') + stderr.read().decode('utf-8', errors='ignore')

print('=== 1. LIMPANDO TABELAS QUE FALHARAM ===')
run("clickhouse-client -q 'TRUNCATE TABLE hemn_update_tmp.estabelecimento'")
run("clickhouse-client -q 'TRUNCATE TABLE hemn_update_tmp.socios'")
print("Tabelas estabelecimento e socios limpas.")

print('\n=== 2. ATUALIZANDO STATUS NO DASHBOARD (SQLite) ===')
db_path = "/var/www/hemn_cloud/hemn_cloud.db"
# Update progress to 5.1% and status to IN_PROGRESS (so it shows up again)
query = "UPDATE background_tasks SET status='IN_PROGRESS', progress=5.1, message='Retomando ingestão: Processando Estabelecimentos e Sócios...' WHERE id='db_update_march_2026';"
run(f'sqlite3 {db_path} "{query}"')
print("Status da tarefa atualizado para IN_PROGRESS.")

print('\n=== 3. INICIANDO SCRIPT DE INGESTÃO EM SEGUNDO PLANO ===')
# Run using nohup to keep it alive
run("nohup python3 /var/www/hemn_cloud/vps_ingest_march_2026.py > /var/www/hemn_cloud/ingest_resume.log 2>&1 &")
print("Script vps_ingest_march_2026.py iniciado em segundo plano.")

client.close()
