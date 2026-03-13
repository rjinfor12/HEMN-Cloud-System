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

print('=== INSPECAO DOS ARQUIVOS DE RESULTADO ===')
print(run('ls -lh /var/www/hemn_cloud/storage/results/ | tail -n 5'))

print('\n=== TESTANDO QUERY CLICKHOUSE PARA UM CNPJ DO PRINT ===')
# CNPJ: 54560969000146 (do print do usuário)
cnpj = "54560969000146"
basico = cnpj[:8]
ordem = cnpj[8:12]
dv = cnpj[12:]

q = f"""
SELECT 
    e.razao_social, 
    estab.cnpj_basico,
    estab.logradouro,
    estab.numero,
    estab.bairro,
    estab.uf,
    estab.cep,
    estab.telefone1
FROM hemn.estabelecimento estab
JOIN hemn.empresas e ON estab.cnpj_basico = e.cnpj_basico
WHERE estab.cnpj_basico = '{basico}' 
  AND estab.cnpj_ordem = '{ordem}' 
  AND estab.cnpj_dv = '{dv}'
LIMIT 1
"""

# Usando o client do clickhouse via terminal
print(run(f"clickhouse-client --query \"{q}\""))

client.close()
