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

print("--- hemn.socios Schema ---")
res = ch.query("DESCRIBE TABLE hemn.socios")
for r in res.result_rows:
    print(r)

print("\\n--- Sample data from hemn.socios for Rogerio ---")
res = ch.query("SELECT * FROM hemn.socios WHERE nome_socio LIKE '%ROGERIO ELIAS DO NASCIMENTO JUNIOR%' LIMIT 5")
for r in res.result_rows:
    print(r)
"""

sftp = client.open_sftp()
with sftp.file('/tmp/check_socios_schema.py', 'w') as f:
    f.write(python_script)
sftp.close()

stdin, stdout, stderr = client.exec_command("/var/www/hemn_cloud/venv/bin/python /tmp/check_socios_schema.py")
print(stdout.read().decode('utf-8'))
client.close()
