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

# Check Rogerio's exact establishment data
print("--- Rogerio establishments ---")
res = ch.query(\"\"\"
SELECT cnpj_basico, cnpj_ordem, cnpj_dv, situacao_cadastral, ddd1, telefone1, ddd2, telefone2, uf
FROM hemn.estabelecimento
WHERE cnpj_basico = '18528540'
\"\"\")
for r in res.result_rows:
    print(r)

# Check format of situacao_cadastral in general
print("\\n--- Distinct situacao_cadastral values (sample) ---")
res2 = ch.query("SELECT DISTINCT situacao_cadastral FROM hemn.estabelecimento LIMIT 20")
print(res2.result_rows)

# Check after my zfill(2) — what does '2' become vs '02'
sample = ch.query("SELECT situacao_cadastral, length(situacao_cadastral) as len FROM hemn.estabelecimento WHERE cnpj_basico='18528540'")
print("\\n--- Length check ---")
print(sample.result_rows)
"""

sftp = client.open_sftp()
with sftp.file('/tmp/chk_situacao.py', 'w') as f:
    f.write(python_script)
sftp.close()

stdin, stdout, stderr = client.exec_command("/var/www/hemn_cloud/venv/bin/python /tmp/chk_situacao.py")
print(stdout.read().decode('utf-8'))
err = stderr.read().decode('utf-8')
if err: print("ERR:", err)
client.close()
