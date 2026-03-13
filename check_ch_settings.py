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

print('=== VERSÃO DO CLICKHOUSE ===')
print(run("clickhouse-client --query 'SELECT version()'"))

print('\n=== VERIFICANDO SETTINGS DISPONÍVEIS ===')
print(run("clickhouse-client --query \"SELECT name FROM system.settings WHERE name LIKE '%external_join%' OR name LIKE '%bytes_in_join%'\""))

client.close()
