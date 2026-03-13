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

print('--- SEARCHING MEI IN EMPRESAS ---')
q1 = "SELECT razao_social, cnpj_basico FROM hemn.empresas WHERE razao_social LIKE '%ROGERIO%' AND razao_social LIKE '%9752279473%'"
res1 = client.query(q1)
for r in res1.result_rows: print(r)

print('\\n--- SEARCHING MEI BY NAME ONLY ---')
q2 = "SELECT razao_social, cnpj_basico FROM hemn.empresas WHERE razao_social LIKE '%ROGERIO ELIAS DO NASCIMENTO JUNIOR%'"
res2 = client.query(q2)
for r in res2.result_rows: print(r)
"""

sftp = client.open_sftp()
with sftp.file('/tmp/diag_rogerio_mei_fixed.py', 'w') as f:
    f.write(python_script)
sftp.close()

cmd = "/var/www/hemn_cloud/venv/bin/python /tmp/diag_rogerio_mei_fixed.py"
stdin, stdout, stderr = client.exec_command(cmd)

print("STDOUT:")
print(stdout.read().decode('utf-8'))
print("STDERR:")
print(stderr.read().decode('utf-8'))
client.close()
