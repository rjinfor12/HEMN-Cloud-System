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

print('=== LISTANDO USUARIOS NA VPS ===')
db_path = "/var/www/hemn_cloud/hemn_cloud.db"
# Seleciona username e as primeiras 3 letras da senha pra não expor tudo nos logs se possível, mas aqui precisamos ver se bate
query = "SELECT username, password, status, role FROM users;"
r = run(f'sqlite3 {db_path} "{query}"')
print(r)

client.close()cu
