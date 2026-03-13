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

print('=== MENSAGEM FINAL DA TAREFA 9C2025E0 ===')
q = "SELECT message FROM background_tasks WHERE id LIKE '9c2025e0%'"
print(run(f'sqlite3 /var/www/hemn_cloud/hemn_cloud.db "{q}"'))

client.close()
