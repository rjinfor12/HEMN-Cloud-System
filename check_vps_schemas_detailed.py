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

tables = ['empresas', 'estabelecimento', 'socios']
print('=== SCHEMAS DAS TABELAS NO hemn ===')
for table in tables:
    print(f"\n--- {table} ---")
    print(run(f"clickhouse-client --query 'DESCRIBE TABLE hemn.{table}'"))

client.close()
