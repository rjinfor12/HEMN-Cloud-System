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

print('=== CONTEUDO DO BACKUP HEMN_DEPLOY.TAR.GZ ===')
print(run("tar -ztvf /var/www/hemn_cloud/hemn_deploy.tar.gz | grep cloud_engine.py"))

# Se existir, vamos extrair para um local temporario para ler
print('\n=== LENDO VERSAO DO BACKUP ===')
run("tar -zxf /var/www/hemn_cloud/hemn_deploy.tar.gz -C /tmp cloud_engine.py")
print(run("sed -n '700,800p' /tmp/cloud_engine.py"))

client.close()
