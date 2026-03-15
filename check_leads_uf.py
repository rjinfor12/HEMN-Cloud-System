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

print("--- hemn.leads UF distribution ---")
res = ch.query("SELECT uf, count(*) FROM hemn.leads GROUP BY uf ORDER BY count(*) DESC LIMIT 20")
for r in res.result_rows:
    print(r)

print("\\n--- Checking for ROGERIO in hemn.leads (ANY UF) ---")
res = ch.query("SELECT DISTINCT nome, uf FROM hemn.leads WHERE nome LIKE '%ROGERIO ELIAS%'")
for r in res.result_rows:
    print(r)
"""

sftp = client.open_sftp()
with sftp.file('/tmp/check_leads_uf.py', 'w') as f:
    f.write(python_script)
sftp.close()

stdin, stdout, stderr = client.exec_command("/var/www/hemn_cloud/venv/bin/python /tmp/check_leads_uf.py")
print(stdout.read().decode('utf-8'))
client.close()
