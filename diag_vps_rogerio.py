import paramiko
import time

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = r'C:\Users\Junior T.I\.ssh\id_rsa'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)

python_script = """import clickhouse_connect
import re

def smart_pad(val):
    clean = re.sub(r'\\D', '', str(val))
    if 9 <= len(clean) <= 10:
        return clean.zfill(11)
    return clean

# Test normalization
input_cpf = "9752279473"
padded = smart_pad(input_cpf)
print(f"Input: {input_cpf} -> Padded: {padded}")

client = clickhouse_connect.get_client(host='localhost', username='default', password='', port=8123)

# 1. Verify existence in Empresas
q1 = f"SELECT cnpj_basico, razao_social FROM hemn.empresas WHERE razao_social LIKE '%{padded}%' OR razao_social LIKE '%ROGERIO ELIAS DO NASCIMENTO JUNIOR%'"
res1 = client.query(q1)
print(f"Search in Empresas results: {res1.result_rows}")

# 2. Test multiSearchFirstIndex logic
patterns = [padded, '***522794**']
patterns_str = ", ".join([f"'{p}'" for p in patterns])

razao_social = 'ROGERIO ELIAS DO NASCIMENTO JUNIOR 09752279473'
q2 = f"SELECT multiSearchFirstIndex('{razao_social}', [{patterns_str}]) as p_idx"
res2 = client.query(q2)
print(f"multiSearchFirstIndex test with {razao_social}: {res2.result_rows}")

# 3. Test if smart_pad approach would find it in a real query
q3 = f\"\"\"
SELECT DISTINCT e.cnpj_basico, '{padded}' as original_search
FROM hemn.empresas e
WHERE multiSearchAny(razao_social, ['{padded}'])
  AND positionCaseInsensitiveUTF8(razao_social, 'ROGERIO ELIAS DO NASCIMENTO JUNIOR') > 0
\"\"\"
res3 = client.query(q3)
print(f"Full query simulation results: {res3.result_rows}")
"""

sftp = client.open_sftp()
with sftp.file('/tmp/diag_rogerio.py', 'w') as f:
    f.write(python_script)
sftp.close()

cmd = "/var/www/hemn_cloud/venv/bin/python /tmp/diag_rogerio.py"
stdin, stdout, stderr = client.exec_command(cmd)

print("STDOUT:")
print(stdout.read().decode('utf-8'))
print("STDERR:")
print(stderr.read().decode('utf-8'))
client.close()
