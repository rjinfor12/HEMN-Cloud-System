import paramiko, os
host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)
stdin, stdout, stderr = client.exec_command('journalctl -u hemn_cloud -n 1000')
logs = stdout.read().decode('utf-8', errors='replace')
lines = [l for l in logs.split('\n') if 'Consultando' in l or 'Processando' in l or 'Excluindo' in l or 'Identificando' in l]
for l in lines[-30:]:
    print(l)
client.close()
