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

print('=== ULTIMAS TAREFAS (background_tasks) NA VPS ===')
db_path = "/var/www/hemn_cloud/hemn_cloud.db"
query = "SELECT id, status, progress, message, module, username FROM background_tasks ORDER BY created_at DESC LIMIT 10;"
r = run(f'sqlite3 {db_path} "{query}"')
print(r)

client.close()
