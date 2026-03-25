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
    return stdout.read().decode('utf-8', errors='ignore') + stderr.read().decode('utf-8', errors='ignore')

print('=== VERIFICANDO PROCESSO DE INGESTÃO ===')
r = run('ps aux | grep vps_ingest_march_2026.py | grep -v grep')
print(r if r.strip() else "Processo não encontrado.")

print('\n=== VERIFICANDO TAMANHO DO LOG PRINCIPAL ===')
r = run('ls -lh /var/www/hemn_cloud/ingest_march_2026.log')
print(r)

print('\n=== ÚLTIMAS 5 LINHAS DO LOG PRINCIPAL ===')
r = run('tail -n 5 /var/www/hemn_cloud/ingest_march_2026.log')
print(r)

client.close()
