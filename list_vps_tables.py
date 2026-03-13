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
res = client.query("SHOW TABLES FROM hemn")
print(res.result_rows)
"""

sftp = client.open_sftp()
with sftp.file('/tmp/list_tables.py', 'w') as f:
    f.write(python_script)
sftp.close()

stdin, stdout, stderr = client.exec_command("/var/www/hemn_cloud/venv/bin/python /tmp/list_tables.py")
print(stdout.read().decode('utf-8'))
client.close()
