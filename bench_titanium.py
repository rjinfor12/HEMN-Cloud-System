import paramiko
import time

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = r'C:\Users\Junior T.I\.ssh\id_rsa'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)

python_script = """import clickhouse_connect
import time
client = clickhouse_connect.get_client(host='localhost', username='default', password='', port=8123)

patterns = ['09752279473', '11111111111', '22222222222'] * 33 # 99 patterns
patterns_str = ", ".join([f"'{c}'" for c in patterns])

start = time.time()
q = f\"\"\"
SELECT count() 
FROM hemn.empresas 
WHERE multiSearchAny(razao_social, [{patterns_str}])
\"\"\"
res = client.query(q)
end = time.time()

print(f"Scan of 66M rows for 99 CPFs took: {end - start:.2f} seconds")
print(f"Found: {res.result_rows[0][0]} rows")
"""

sftp = client.open_sftp()
with sftp.file('/tmp/bench_titanium.py', 'w') as f:
    f.write(python_script)
sftp.close()

cmd = "/var/www/hemn_cloud/venv/bin/python /tmp/bench_titanium.py"
stdin, stdout, stderr = client.exec_command(cmd)

print("STDOUT:")
print(stdout.read().decode('utf-8'))
print("STDERR:")
print(stderr.read().decode('utf-8'))
client.close()
