import paramiko, os, sys

sys.stdout.reconfigure(encoding='utf-8')

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username='root', key_filename=key_path)

def run(cmd):
    stdin, stdout, stderr = client.exec_command(cmd)
    stdout.channel.recv_exit_status()
    return stdout.read().decode('utf-8', errors='replace') + stderr.read().decode('utf-8', errors='replace')

# Ajuste global do cliente ClickHouse
patch_script = r'''
with open('/var/www/hemn_cloud/cloud_engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_conn = "return clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='')"
new_conn = "return clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='', settings={'max_query_size': 10485760})"

content = content.replace(old_conn, new_conn)

with open('/var/www/hemn_cloud/cloud_engine.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Configuração global de max_query_size aplicada.")
'''

sftp = client.open_sftp()
with sftp.open('/tmp/fix_global_ch_limit.py', 'w') as f:
    f.write(patch_script)
sftp.close()

print(run("/var/www/hemn_cloud/venv/bin/python3 /tmp/fix_global_ch_limit.py 2>&1"))

# Reiniciar
run("systemctl restart hemn_cloud.service")

# Sincronizar para o Git Local
local_path = r"C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\cloud_engine.py"
remote_path = "/var/www/hemn_cloud/cloud_engine.py"
sftp = client.open_sftp()
sftp.get(remote_path, local_path)
sftp.close()

client.close()
