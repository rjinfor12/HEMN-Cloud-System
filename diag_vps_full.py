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
client = clickhouse_connect.get_client(host='localhost', username='default', password='', port=8123)

# 1. Check if the MEI basico is in full_view
print("--- FULL VIEW CHECK (18528540) ---")
res1 = client.query("SELECT cnpj_basico, cnpj_completo, razao_social FROM hemn.full_view WHERE cnpj_basico = '18528540'")
print(f"Results: {res1.result_rows}")

# 2. Check if the other company is in full_view
print("\\n--- FULL VIEW CHECK (38262186) ---")
res2 = client.query("SELECT cnpj_basico, cnpj_completo, razao_social FROM hemn.full_view WHERE cnpj_basico = '38262186'")
print(f"Results: {res2.result_rows}")

# 3. Check socios for both
print("\\n--- SOCIOS CHECK ---")
res3 = client.query("SELECT cnpj_basico, nome_socio, cnpj_cpf_socio FROM hemn.socios WHERE cnpj_basico IN ('18528540', '38262186')")
print(f"Socios: {res3.result_rows}")

# 4. Check if Rogerio exists anywhere in socios
print("\\n--- GLOBAL SOCIOS CHECK (NAME MATCH) ---")
res4 = client.query("SELECT cnpj_basico, nome_socio, cnpj_cpf_socio FROM hemn.socios WHERE nome_socio LIKE '%ROGERIO ELIAS DO NASCIMENTO JUNIOR%'")
print(f"Rogerio in Socios: {res4.result_rows}")
"""

sftp = client.open_sftp()
with sftp.file('/tmp/diag_full_rogerio.py', 'w') as f:
    f.write(python_script)
sftp.close()

cmd = "/var/www/hemn_cloud/venv/bin/python /tmp/diag_full_rogerio.py"
stdin, stdout, stderr = client.exec_command(cmd)

print("STDOUT:")
print(stdout.read().decode('utf-8'))
print("STDERR:")
print(stderr.read().decode('utf-8'))
client.close()
