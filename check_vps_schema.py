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
print("--- empresas ---")
res1 = client.query("DESCRIBE hemn.empresas")
for r in res1.result_rows: print(r)

print("\\n--- estabelecimento ---")
res2 = client.query("DESCRIBE hemn.estabelecimento")
for r in res2.result_rows: print(r)
"""

sftp = client.open_sftp()
with sftp.file('/tmp/check_schema.py', 'w') as f:
    f.write(python_script)
sftp.close()

stdin, stdout, stderr = client.exec_command("/var/www/hemn_cloud/venv/bin/python /tmp/check_schema.py")
print(stdout.read().decode('utf-8'))
client.close()
