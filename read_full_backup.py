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

# Extrair a versão estável do backup para comparação completa
run("tar -zxf /var/www/hemn_cloud/hemn_deploy.tar.gz -C /tmp cloud_engine.py")

print('=== LENDO LOGICA DE EXTRAÇÃO DO BACKUP ===')
# Lendo a função _run_extraction completa do backup
print(run("sed -n '600,950p' /tmp/cloud_engine.py"))

client.close()
