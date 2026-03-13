import paramiko

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = r'C:\Users\Junior T.I\.ssh\id_rsa'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)

python_script = """import clickhouse_connect
ch = clickhouse_connect.get_client(host='localhost', username='default', password='', port=8123)

# Check if Rogerio's CPF is in socios for the ATIVA company
print("--- Socios search with CPF 09752279473 ---")
res = ch.query("SELECT cnpj_basico, nome_socio, cnpj_cpf_socio FROM hemn.socios WHERE cnpj_basico = '38262186'")
for r in res.result_rows:
    print(r)

# Try searching by the 11-digit CPF
print("\\n--- CPF search in socios ---")
res2 = ch.query("SELECT cnpj_basico, nome_socio, cnpj_cpf_socio FROM hemn.socios WHERE cnpj_cpf_socio = '09752279473'")
print(res2.result_rows)

# Try searching by 10-digit (Excel-stripped)
print("\\n--- 10-digit CPF search ---")
res3 = ch.query("SELECT cnpj_basico, nome_socio, cnpj_cpf_socio FROM hemn.socios WHERE cnpj_cpf_socio = '9752279473'")
print(res3.result_rows)

# Check how CPF is stored in socios
print("\\n--- CPF field length in socios for this company ---")
res4 = ch.query("SELECT cnpj_cpf_socio, length(cnpj_cpf_socio) FROM hemn.socios WHERE cnpj_basico = '38262186'")
print(res4.result_rows)

# Check the mask approach ***522794**
print("\\n--- Mask approach for 38262186 ---")
res5 = ch.query("SELECT cnpj_basico, nome_socio, cnpj_cpf_socio FROM hemn.socios WHERE cnpj_basico = '38262186' AND nome_socio LIKE '%ROGERIO ELIAS%'")
print(res5.result_rows)
"""

sftp = client.open_sftp()
with sftp.file('/tmp/chk_socios.py', 'w') as f:
    f.write(python_script)
sftp.close()

stdin, stdout, stderr = client.exec_command("/var/www/hemn_cloud/venv/bin/python /tmp/chk_socios.py")
print(stdout.read().decode('utf-8'))
client.close()
