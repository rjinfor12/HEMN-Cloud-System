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

print("--- hemn.leads UF Counts ---")
res = ch.query("SELECT uf, count(*) FROM hemn.leads GROUP BY uf ORDER BY count(*) DESC")
for r in res.result_rows:
    print(r)

print("\\n--- hemn.leads Sample from PE ---")
res = ch.query("SELECT * FROM hemn.leads WHERE uf = 'PE' LIMIT 10")
for r in res.result_rows:
    print(r)

print("\\n--- Checking for ROGERIO in hemn.socios (Searching for CPF/NAME) ---")
# ROGERIO ELIAS DO NASCIMENTO JUNIOR 09752279473
res = ch.query(\"\"\"
    SELECT s.nome_socio, s.cnpj_cpf_socio, e.razao_social, e.uf
    FROM hemn.socios s
    JOIN hemn.estabelecimento e ON s.cnpj_basico = e.cnpj_basico
    WHERE s.nome_socio LIKE '%ROGERIO ELIAS DO NASCIMENTO%' OR s.cnpj_cpf_socio LIKE '%09752279473%'
    LIMIT 10
\"\"\")
for r in res.result_rows:
    print(r)
"""

sftp = client.open_sftp()
with sftp.file('/tmp/check_pe_data.py', 'w') as f:
    f.write(python_script)
sftp.close()

stdin, stdout, stderr = client.exec_command("/var/www/hemn_cloud/venv/bin/python /tmp/check_pe_data.py")
print(stdout.read().decode('utf-8'))
client.close()
