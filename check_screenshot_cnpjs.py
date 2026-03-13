import paramiko, os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

# CNPJs da print:
# 54573264000163
# 54573280000156
# 54573288000112

diag_script = r"""
import sys
import os
sys.path.append('/var/www/hemn_cloud')
from cloud_engine import CloudEngine

engine = CloudEngine()

cnpjs = ['54573264000163', '54573280000156', '54573288000112']
basicos = [c[:8] for c in cnpjs]

print(f"--- TESTING CNPJ BASICOS: {basicos} ---")

# Test 1: Do they exist in empresas?
q1 = f"SELECT cnpj_basico, razao_social FROM hemn.empresas WHERE cnpj_basico IN {tuple(basicos)}"
res1 = engine.ch_client.query(q1)
print(f"MATCHES IN EMPRESAS: {res1.result_rows}")

# Test 2: Do they exist in estabelecimento?
q2 = f"SELECT cnpj_basico, cnpj_ordem, cnpj_dv, logradouro FROM hemn.estabelecimento WHERE cnpj_basico IN {tuple(basicos)} LIMIT 10"
res2 = engine.ch_client.query(q2)
print(f"MATCHES IN ESTABELECIMENTO: {res2.result_rows}")

# Test 3: Raw JOIN result for one
q3 = f'''
    SELECT 
        e.razao_social, 
        estab.cnpj_basico, 
        estab.logradouro
    FROM hemn.empresas e
    INNER JOIN hemn.estabelecimento estab ON e.cnpj_basico = estab.cnpj_basico
    WHERE e.cnpj_basico = '{basicos[0]}'
    LIMIT 1
'''
res3 = engine.ch_client.query(q3)
print(f"RAW JOIN RESULT (Single): {res3.result_rows}")
"""

print('=== VERIFICANDO CNPJS DA SCREENSHOT NA VPS ===')
client.exec_command("cat << 'EOF' > /tmp/check_screenshot_cnpjs.py\n" + diag_script + "\nEOF")
stdin, stdout, stderr = client.exec_command("/var/www/hemn_cloud/venv/bin/python3 /tmp/check_screenshot_cnpjs.py")
print(stdout.read().decode('utf-8', errors='replace'))
print(stderr.read().decode('utf-8', errors='replace'))

client.close()
