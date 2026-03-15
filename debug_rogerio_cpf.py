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

print("--- Searching by CPF 09752279473 in hemn.leads ---")
res = ch.query("SELECT * FROM hemn.leads WHERE cpf = '09752279473'")
print(f"Found {len(res.result_rows)} records")
for r in res.result_rows:
    print(r)

print("\\n--- Searching by Name 'ROGERIO ELIAS DO NASCIMENTO JUNIOR' in hemn.leads ---")
res = ch.query("SELECT * FROM hemn.leads WHERE nome = 'ROGERIO ELIAS DO NASCIMENTO JUNIOR'")
print(f"Found {len(res.result_rows)} records")
for r in res.result_rows:
    print(r)
"""

sftp = client.open_sftp()
with sftp.file('/tmp/debug_rogerio_cpf.py', 'w') as f:
    f.write(python_script)
sftp.close()

stdin, stdout, stderr = client.exec_command("/var/www/hemn_cloud/venv/bin/python /tmp/debug_rogerio_cpf.py")
print(stdout.read().decode('utf-8'))
client.close()
