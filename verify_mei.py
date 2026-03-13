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

print('=== VERIFICANDO NATUREZA JURIDICA PARA MEI ===')
# Busca empresas que tenham "MEI" ou "INDIVIDUAL" no nome para ver a natureza_juridica
q = "SELECT natureza_juridica, count(*) FROM hemn.empresas WHERE razao_social LIKE '% MEI%' GROUP BY natureza_juridica ORDER BY count(*) DESC LIMIT 5"
print(run(f"clickhouse-client --query \"{q}\""))

print('\n=== VERIFICANDO POR NATUREZA 2135 ===')
q2 = "SELECT razao_social FROM hemn.empresas WHERE natureza_juridica = '2135' LIMIT 5"
print(run(f"clickhouse-client --query \"{q2}\""))

client.close()
