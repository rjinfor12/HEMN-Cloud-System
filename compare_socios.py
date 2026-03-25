import paramiko

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = r'C:\Users\Junior T.I\.ssh\id_rsa'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)

def get_sqlite_cols(table):
    stdin, stdout, stderr = client.exec_command(f"sqlite3 /var/lib/clickhouse/user_files/cnpj.db 'PRAGMA table_info({table})'")
    lines = stdout.read().decode('utf-8').splitlines()
    return [line.split('|')[1] for line in lines]

def get_clickhouse_cols(table):
    stdin, stdout, stderr = client.exec_command(f"clickhouse-client -q 'DESCRIBE hemn.{table}'")
    lines = stdout.read().decode('utf-8').splitlines()
    return [line.split('\t')[0] for line in lines]

print("Socios SQLite columns:", get_sqlite_cols('socios'))
print("Socios ClickHouse columns:", get_clickhouse_cols('socios'))

client.close()
