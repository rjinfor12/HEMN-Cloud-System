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

print('=== DADOS DO USUARIO ADMIN NA VPS ===')
db_path = "/var/www/hemn_cloud/hemn_cloud.db"
q1 = "SELECT username, total_limit, current_usage, role FROM users WHERE username = 'admin';"
print(run(f'sqlite3 {db_path} "{q1}"'))

print('=== ULTIMAS TRANSACOES NO EXTRATO ===')
q2 = "SELECT id, username, type, amount, module, description, timestamp FROM credit_transactions ORDER BY timestamp DESC LIMIT 10;"
print(run(f'sqlite3 {db_path} "{q2}"'))

client.close()
