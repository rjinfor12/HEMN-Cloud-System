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

# Historico completo de todas as transacoes do usuario Vt
print("=== HISTORICO COMPLETO DO USUARIO Vt ===")
print(run("sqlite3 /var/www/hemn_cloud/hemn_cloud.db \"SELECT type, amount, module, description, timestamp FROM credit_transactions WHERE username = 'Vt' ORDER BY timestamp ASC;\""))

# Ver a estrutura da tabela users
print("=== ESTRUTURA DA TABELA USERS ===")
print(run("sqlite3 /var/www/hemn_cloud/hemn_cloud.db 'PRAGMA table_info(users);'"))

client.close()
