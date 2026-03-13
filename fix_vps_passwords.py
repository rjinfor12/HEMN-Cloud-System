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

print('=== RESETANDO SENHAS NA VPS ===')
db_path = "/var/www/hemn_cloud/hemn_cloud.db"
# Muda a senha do admin para 'admin' e do Vt para 'admin' também para facilitar o teste inicial
query = "UPDATE users SET password = 'admin' WHERE username = 'admin'; UPDATE users SET password = 'admin' WHERE username = 'Vt';"
r = run(f'sqlite3 {db_path} "{query}"')
print("Update result:", r)

print('=== CONFERINDO TABELA DE USUARIOS ===')
query = "SELECT username, password, status, role FROM users;"
r = run(f'sqlite3 {db_path} "{query}"')
print(r)

client.close()
