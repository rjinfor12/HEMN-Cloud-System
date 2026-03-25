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

print('=== CRIANDO TABELA hemn._metadata ===')
create_sql = "CREATE TABLE IF NOT EXISTS hemn._metadata (key String, value String) ENGINE = MergeTree() ORDER BY key"
run(f"clickhouse-client --query '{create_sql}'")

print('=== INICIALIZANDO COM Janeiro/2026 ===')
insert_sql = "INSERT INTO hemn._metadata (key, value) VALUES (\\'db_version\\', \\'Janeiro/2026\\')"
run(f"clickhouse-client --query \"{insert_sql}\"")

print('=== VERIFICANDO ===')
print(run("clickhouse-client --query 'SELECT * FROM hemn._metadata'"))

client.close()
