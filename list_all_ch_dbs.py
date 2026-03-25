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

print('=== LISTA DE DATABASES CLICKHOUSE ===')
print(run("clickhouse-client --query 'SHOW DATABASES'"))

print('\n=== TABELAS EM OUTROS DATABASES ===')
databases = run("clickhouse-client --query 'SHOW DATABASES'").splitlines()
for db in databases:
    if db not in ['system', 'information_schema', 'default']:
        print(f'\n--- Database: {db} ---')
        print(run(f"clickhouse-client --query 'SHOW TABLES FROM {db}'"))

client.close()
