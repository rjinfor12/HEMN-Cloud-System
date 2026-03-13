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
    
    # Check if NATUREZA JURIDICA is correct for some CNPJs from the print
    cnpjs = ['54573264', '54573280', '54573532', '54573726']
    for c in cnpjs:
        res = client.query(f"SELECT razao_social, natureza_juridica FROM hemn.empresas WHERE cnpj_basico = '{c}'")
        if res.result_rows:
            print(f"CNPJ {c}: Name='{res.result_rows[0][0]}', Nature='{res.result_rows[0][1]}'")
        else:
            print(f"CNPJ {c} NOT FOUND in empresas")

    # Now verify the JOIN logic with a forced small result
    q = '''
        SELECT e.razao_social, e.natureza_juridica, estab.uf
        FROM (
            SELECT cnpj_basico, uf FROM hemn.estabelecimento WHERE uf = 'CE' LIMIT 10
        ) as estab
        JOIN hemn.empresas e ON e.cnpj_basico = estab.cnpj_basico
    '''
    res = client.query(q)
    print("\nSample Join Result:")
    for row in res.result_rows:
        print(row)

except Exception as e:
    print(f"Erro: {e}")
"""

print('=== VERIFICANDO DADOS E JOIN NA VPS ===')
client.exec_command("cat << 'EOF' > /tmp/diag_verify.py\n" + diag_script + "\nEOF")
stdin, stdout, stderr = client.exec_command("/var/www/hemn_cloud/venv/bin/python3 /tmp/diag_verify.py")
print(stdout.read().decode('utf-8', errors='replace'))
print(stderr.read().decode('utf-8', errors='replace'))

client.close()
