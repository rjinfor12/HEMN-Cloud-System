import paramiko

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = r'C:\Users\Junior T.I\.ssh\id_rsa'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)

def check_sqlite(table):
    stdin, stdout, stderr = client.exec_command(f"sqlite3 /var/lib/clickhouse/user_files/cnpj.db 'PRAGMA table_info({table})'")
    cols = stdout.read().decode('utf-8').splitlines()
    print(f"SQLite {table}: {len(cols)} columns")

def check_clickhouse(table):
    cmd = f"clickhouse-client -q 'DESCRIBE hemn.{table}'"
    stdin, stdout, stderr = client.exec_command(cmd)
    cols = stdout.read().decode('utf-8').splitlines()
    print(f"ClickHouse {table}: {len(cols)} columns")

for t in ["empresas", "socios", "municipio"]:
    check_sqlite(t)
    check_clickhouse(t)

client.close()
