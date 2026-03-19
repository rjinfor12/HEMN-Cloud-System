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

# Corrigir batch_size de 500 para 200 para multiSearchAny
patch_script = r'''
with open('/var/www/hemn_cloud/cloud_engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Substituir batch_size=500 por batch_size=200 nas chamadas do multiSearchAny
content = content.replace("batch_size=500", "batch_size=200")

with open('/var/www/hemn_cloud/cloud_engine.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Batch size reduzido para 200.")
'''

sftp = client.open_sftp()
with sftp.open('/tmp/fix_clickhouse_limit.py', 'w') as f:
    f.write(patch_script)
sftp.close()

print(run("/var/www/hemn_cloud/venv/bin/python3 /tmp/fix_clickhouse_limit.py 2>&1"))

# Reiniciar
run("systemctl restart hemn_cloud.service")

# Sincronizar para o Git Local
local_path = r"C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\cloud_engine.py"
remote_path = "/var/www/hemn_cloud/cloud_engine.py"
sftp = client.open_sftp()
sftp.get(remote_path, local_path)
sftp.close()

client.close()
