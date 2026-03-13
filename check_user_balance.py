import paramiko, os

host = '129.121.45.136'
port = 22022
user_ssh = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user_ssh, key_filename=key_path)

def run(cmd):
    stdin, stdout, stderr = client.exec_command(cmd)
    stdout.channel.recv_exit_status()
    return stdout.read().decode('utf-8', errors='replace') + stderr.read().decode('utf-8', errors='replace')

# Verificar o saldo atual do usuario Vt e todos os usuarios
print("=== SALDO DE TODOS OS USUARIOS ===")
print(run("sqlite3 /var/www/hemn_cloud/hemn_cloud.db 'SELECT username, full_name, total_limit, current_usage, (total_limit - current_usage) as saldo FROM users ORDER BY username;'"))

print("=== HISTORICO DE CREDITOS DO USUARIO Vt ===")
print(run("sqlite3 /var/www/hemn_cloud/hemn_cloud.db \"SELECT type, amount, module, description, timestamp FROM credit_transactions WHERE username = 'Vt' ORDER BY timestamp DESC LIMIT 15;\""))

print("=== TODOS PAGAMENTOS ASAAS DO USUARIO Vt ===")
print(run("sqlite3 /var/www/hemn_cloud/hemn_cloud.db \"SELECT id, amount, credits, status, created_at, confirmed_at FROM asaas_payments WHERE username = 'Vt' ORDER BY rowid DESC;\""))

client.close()
