import paramiko, os, sys

sys.stdout.reconfigure(encoding='utf-8')

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username='root', key_filename=key_path)

def run(cmd):
    stdin, stdout, stderr = client.exec_command(cmd)
    stdout.channel.recv_exit_status()
    return stdout.read().decode('utf-8', errors='replace') + stderr.read().decode('utf-8', errors='replace')

test_script = r'''
import clickhouse_connect
import time

ch = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='', settings={'max_query_size': 10485760})

name = 'ROGERIO ELIAS DO NASCIMENTO JUNIOR'
q_template = """
                SELECT 
                    s.nome_socio AS lookup_key,
                    e.razao_social AS razao_social, 
                    estab.cnpj_basico AS cnpj_basico, 
                    estab.situacao_cadastral AS situacao_cadastral
                FROM hemn.socios AS s
                INNER JOIN hemn.empresas AS e ON s.cnpj_basico = e.cnpj_basico
                INNER JOIN hemn.estabelecimento AS estab ON e.cnpj_basico = estab.cnpj_basico
                WHERE s.nome_socio IN %(keys)s
                ORDER BY (estab.situacao_cadastral = '02') DESC
                LIMIT 100
"""

print(f"Executando query para o nome: {name}...")
start = time.time()
res = ch.query(q_template, {'keys': [name]})
end = time.time()

print(f"Tempo decorrido: {end - start:.2f}s")
print(f"Resultados encontrados: {len(res.result_rows)}")
if res.result_rows:
    print(f"Primeira linha: {res.result_rows[0]}")
'''

sftp = client.open_sftp()
with sftp.open('/tmp/diag_latency.py', 'w') as f:
    f.write(test_script)
sftp.close()

print(run("/var/www/hemn_cloud/venv/bin/python3 /tmp/diag_latency.py 2>&1"))
client.close()
