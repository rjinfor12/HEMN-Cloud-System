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

print("--- Searching 'ROGERIO' in hemn.leads ---")
res = ch.query(\"\"\"
SELECT DISTINCT cpf, nome, dt_nascimento, uf, regiao 
FROM hemn.leads 
WHERE nome LIKE '%ROGERIO%' 
LIMIT 50
\"\"\")
print(f"Found {len(res.result_rows)} rows matching 'ROGERIO'")
for r in res.result_rows:
    print(r)

print("\\n--- Searching 'ELIAS DO NASCIMENTO' in hemn.leads ---")
res = ch.query(\"\"\"
SELECT DISTINCT cpf, nome, dt_nascimento, uf, regiao 
FROM hemn.leads 
WHERE nome LIKE '%ELIAS DO NASCIMENTO%' 
LIMIT 50
\"\"\")
print(f"Found {len(res.result_rows)} rows matching 'ELIAS DO NASCIMENTO'")
for r in res.result_rows:
    print(r)

print("\\n--- Table Schema for hemn.leads ---")
res = ch.query("DESCRIBE TABLE hemn.leads")
for r in res.result_rows:
    print(r)
"""

sftp = client.open_sftp()
with sftp.file('/tmp/debug_pf_rogerio.py', 'w') as f:
    f.write(python_script)
sftp.close()

stdin, stdout, stderr = client.exec_command("/var/www/hemn_cloud/venv/bin/python /tmp/debug_pf_rogerio.py")
print("STDOUT:")
print(stdout.read().decode('utf-8'))
print("STDERR:")
print(stderr.read().decode('utf-8'))
client.close()
