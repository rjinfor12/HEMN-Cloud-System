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

print('=== TESTANDO METADADOS DO CLICKHOUSE-CONNECT NO VPS ===')
script = """
import clickhouse_connect
import pandas as pd

client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='')
q = "SELECT 1 as TEST_COL, 'abc' as Another_Col LIMIT 1"
res = client.query(q)
print('Column names:', res.column_names)

# Testando com a query real (parcial)
q2 = "SELECT e.razao_social as NOME_DA_EMPRESA, estab.logradouro as LOGRADOURO FROM hemn.estabelecimento estab JOIN hemn.empresas e ON estab.cnpj_basico = e.cnpj_basico LIMIT 1"
res2 = client.query(q2)
print('Real column names:', res2.column_names)
"""

# Usando heredoc
client.exec_command("cat << 'EOF' > /tmp/test_ch_cols.py\n" + script + "\nEOF")
print(run("/var/www/hemn_cloud/venv/bin/python3 /tmp/test_ch_cols.py"))

client.close()
