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
    return stdout.read().decode('utf-8', errors='replace') + stderr.read().decode('utf-8', errors='replace')

print("=== TAREFAS RECENTES NO DB TITANIUM (background_tasks) ===")
print(run("sqlite3 /var/www/hemn_cloud/hemn_cloud.db \"SELECT id, username, module, status, created_at FROM background_tasks ORDER BY created_at DESC LIMIT 10;\""))

print("\n=== LOGS RECENTES DO SERVIDOR ===")
print(run("journalctl -u hemn_cloud.service -n 50 --no-pager"))

client.close()
