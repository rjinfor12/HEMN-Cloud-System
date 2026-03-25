import paramiko, os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

# Comandos para finalizar o puzzle
# Vimos que empresas_old tem 66M (Março) e está em hemn_backup_old
cmds = [
    # Se hemn.empresas existir (versão antiga), movemos para backup com outro nome
    'clickhouse-client -q "RENAME TABLE hemn.empresas TO hemn_backup_old.empresas_VERY_OLD" 2>/dev/null || true',
    
    # Movemos a de Março para o lugar certo
    'clickhouse-client -q "RENAME TABLE hemn_backup_old.empresas_old TO hemn.empresas"',
    
    # Atualizamos a Versão
    'clickhouse-client -q "INSERT INTO hemn._metadata (key, value) VALUES (\'db_version\', \'Março/2026 (Titanium)\') ON DUPLICATE KEY UPDATE value = \'Março/2026 (Titanium)\'"'
]

for c in cmds:
    print(f"Running: {c}")
    stdin, stdout, stderr = client.exec_command(c)
    print(stdout.read().decode().strip())
    err = stderr.read().decode().strip()
    if err: print(f"INFO/ERR: {err}")

client.close()
