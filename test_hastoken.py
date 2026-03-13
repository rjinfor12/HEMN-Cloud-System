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

print("Checking with hasToken...")
q1 = "SELECT razao_social FROM hemn.empresas WHERE hasToken(razao_social, '09752279473')"
res1 = client.query(q1)
print(f"Results with hasToken: {res1.result_rows}")

print("\\nChecking with position...")
q2 = "SELECT razao_social FROM hemn.empresas WHERE position(razao_social, '09752279473') > 0"
res2 = client.query(q2)
print(f"Results with position: {res2.result_rows}")
"""

sftp = client.open_sftp()
with sftp.file('/tmp/test_hastoken.py', 'w') as f:
    f.write(python_script)
sftp.close()

cmd = "/var/www/hemn_cloud/venv/bin/python /tmp/test_hastoken.py"
stdin, stdout, stderr = client.exec_command(cmd)

print("STDOUT:")
print(stdout.read().decode('utf-8'))
print("STDERR:")
print(stderr.read().decode('utf-8'))
client.close()
