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

# Check all companies with Rogerio's CPF / name
print("--- All Empresas with ROGERIO ---")
res = ch.query(\"\"\"
SELECT cnpj_basico, razao_social FROM hemn.empresas
WHERE razao_social LIKE '%ROGERIO ELIAS DO NASCIMENTO JUNIOR%'
\"\"\")
for r in res.result_rows:
    print(r)

# Check all establishments for all Rogerio cnpj_basico results
basico_list = [r[0] for r in res.result_rows]
if basico_list:
    basicos_str = ", ".join([f"'{b}'" for b in basico_list])
    print("\\n--- Establishments for all Rogerio companies ---")
    res2 = ch.query(f\"\"\"
    SELECT cnpj_basico, cnpj_ordem, cnpj_dv, situacao_cadastral, ddd1, telefone1, data_inicio_atividades
    FROM hemn.estabelecimento
    WHERE cnpj_basico IN ({basicos_str})
    \"\"\")
    for r in res2.result_rows:
        print(r)
"""

sftp = client.open_sftp()
with sftp.file('/tmp/chk_rogerio2.py', 'w') as f:
    f.write(python_script)
sftp.close()

stdin, stdout, stderr = client.exec_command("/var/www/hemn_cloud/venv/bin/python /tmp/chk_rogerio2.py")
print(stdout.read().decode('utf-8'))
client.close()
