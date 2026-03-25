import paramiko, os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

# SQL para garantir que a tabela existe e tem a versão
sqls = [
    "CREATE TABLE IF NOT EXISTS hemn._metadata (key String, value String) ENGINE = MergeTree ORDER BY key",
    "ALTER TABLE hemn._metadata DELETE WHERE key = 'db_version'",
    "INSERT INTO hemn._metadata (key, value) VALUES ('db_version', 'Março/2026')"
]

for sql in sqls:
    cmd = f'clickhouse-client -q "{sql}"'
    client.exec_command(cmd)

print("SUCCESS: Metadata updated for March 2026.")
client.close()
