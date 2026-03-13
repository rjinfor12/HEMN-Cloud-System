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

diag_script = r"""
import pandas as pd
import clickhouse_connect

try:
    client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='')
    
    # Put the SMALLER table on the RIGHT for the JOIN
    q = '''
        SELECT count()
        FROM hemn.empresas e
        ANY INNER JOIN (
            SELECT cnpj_basico 
            FROM hemn.estabelecimento 
            WHERE uf = 'CE' AND situacao_cadastral = '02'
        ) as estab ON e.cnpj_basico = estab.cnpj_basico
        WHERE e.natureza_juridica = '2135'
    '''
    res = client.query(q)
    print(f"Count (MEI CE ATIVA): {res.result_rows[0][0]:,}")

except Exception as e:
    print(f"Erro: {e}")
"""

print('=== EXECUTANDO CONTAGEM OTIMIZADA NA VPS ===')
client.exec_command("cat << 'EOF' > /tmp/diag_count.py\n" + diag_script + "\nEOF")
stdin, stdout, stderr = client.exec_command("/var/www/hemn_cloud/venv/bin/python3 /tmp/diag_count.py")
print(stdout.read().decode('utf-8', errors='replace'))
print(stderr.read().decode('utf-8', errors='replace'))

client.close()
