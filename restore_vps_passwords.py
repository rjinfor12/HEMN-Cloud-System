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

print('=== RESTAURANDO SENHAS ORIGINAIS NA VPS ===')
db_path = "/var/www/hemn_cloud/hemn_cloud.db"
# admin123 e 131313 conforme visto anteriormente
query = "UPDATE users SET password = 'admin123' WHERE username = 'admin'; UPDATE users SET password = '131313' WHERE username = 'Vt';"
r = run(f'sqlite3 {db_path} "{query}"')
print("Update result:", r)

print('=== CONFERINDO TABELA DE USUARIOS ===')
query = "SELECT username, password, status FROM users;"
r = run(f'sqlite3 {db_path} "{query}"')
print(r)

client.close()
