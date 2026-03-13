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

print('=== TESTANDO JOIN EM LARGA ESCALA NO CLICKHOUSE ===')
# Testando 100 registros aleatorios
q = "SELECT raz.razao_social, est.logradouro, est.cnpj_basico FROM hemn.estabelecimento est JOIN hemn.empresas raz ON est.cnpj_basico = raz.cnpj_basico LIMIT 100"
print(run(f'clickhouse-client --query "{q}"'))

client.close()
