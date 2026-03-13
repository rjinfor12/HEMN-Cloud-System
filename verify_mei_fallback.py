import paramiko

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = r'C:\Users\Junior T.I\.ssh\id_rsa'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)

python_script = """import clickhouse_connect
client = clickhouse_connect.get_client(host='localhost', username='default', password='', port=8123)

# Simulate the new Part 2 of translation_q for Rogerio Elias
search_term = '09752279473'
target_name = 'ROGERIO ELIAS DO NASCIMENTO JUNIOR'

print(f"Simulating MEI Fallback for CPF {search_term} and Name {target_name}")

q = f\"\"\"
SELECT DISTINCT e.cnpj_basico, '{search_term}' AS original_search
FROM hemn.empresas e 
WHERE length('{search_term}') = 11 
  AND positionCaseInsensitiveUTF8(e.razao_social, '{search_term}') > 0
  AND ('{target_name}' = '' OR positionCaseInsensitiveUTF8(e.razao_social, '{target_name}') > 0)
\"\"\"

res = client.query(q)
print(f"Mei Fallback results: {len(res.result_rows)}")
for row in res.result_rows:
    print(row)
"""

sftp = client.open_sftp()
with sftp.file('/tmp/verify_mei_fallback.py', 'w') as f:
    f.write(python_script)
sftp.close()

cmd = "/var/www/hemn_cloud/venv/bin/python /tmp/verify_mei_fallback.py"
stdin, stdout, stderr = client.exec_command(cmd)

print("STDOUT:")
print(stdout.read().decode('utf-8'))
print("STDERR:")
print(stderr.read().decode('utf-8'))
client.close()
