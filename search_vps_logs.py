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

print('=== BUSCANDO PARAMETROS DE EXTRACAO NOS LOGS ===')
# Busca por mensagens de inicio de extracao
print(run('journalctl -u hemn_cloud.service --since "12 hours ago" | grep "Iniciada" | tail -n 20'))

client.close()
