import paramiko, os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

# 1. Criar banco de backup
client.exec_command('clickhouse-client -q "CREATE DATABASE IF NOT EXISTS hemn_backup_old"')

# 2. Lista de tabelas para trocar
tables = [
    "empresas", "estabelecimento", "socios", "municipio", "paises", 
    "natureza_juridica", "qualificacao_socio", "cnae", "motivo", "simples"
]

# Construir o comando RENAME massivo
# Formato: RENAME TABLE db1.t1 TO db2.t1_old, db3.t1_new TO db1.t1;
rename_parts = []
for t in tables:
    rename_parts.append(f"hemn.{t} TO hemn_backup_old.{t}_{os.urandom(2).hex()}")
    rename_parts.append(f"hemn_update_tmp.{t} TO hemn.{t}")

rename_cmd = f"RENAME TABLE {', '.join(rename_parts)}"

print(f"EXECUTING ATOMIC SWAP...")
stdin, stdout, stderr = client.exec_command(f'clickhouse-client -q "{rename_cmd}"')

out = stdout.read().decode().strip()
err = stderr.read().decode().strip()

if err:
    print(f"ERROR DURING SWAP: {err}")
else:
    print("SUCCESS! Atomic Swap completed.")
    # Atualizar metadados de versão
    client.exec_command('clickhouse-client -q "INSERT INTO hemn._metadata (key, value) VALUES (\'db_version\', \'Março/2026 (Titanium)\') ON DUPLICATE KEY UPDATE value = \'Março/2026 (Titanium)\'"')

client.close()
