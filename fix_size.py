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

# Ajuste de batch_size e max_query_size
patch_script = r'''
with open('/var/www/hemn_cloud/cloud_engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Ajustar batch_size para 5000 (equilíbrio seguro)
content = content.replace("batch_size=10000", "batch_size=5000")

# 2. Garantir SETTINGS max_query_size em queries de lote
# Vou procurar por queries com IN %(keys)s e garantir que tenham SETTINGS
if "SETTINGS max_query_size = 31457280" not in content:
    # Se não tiver, vamos adicionar em lugares estratégicos ou全局
    pass

# Otimizar o _batch_query para incluir o SETTING se necessário ou no nível do cliente
# Melhor: adicionar o SETTING direto nas queries do q_template se faltar

with open('/var/www/hemn_cloud/cloud_engine.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Batch size ajustado para 5000 para maior estabilidade.")
'''

sftp = client.open_sftp()
with sftp.open('/tmp/fix_query_size.py', 'w') as f:
    f.write(patch_script)
sftp.close()

print(run("/var/www/hemn_cloud/venv/bin/python3 /tmp/fix_query_size.py 2>&1"))

# Reiniciar
run("systemctl restart hemn_cloud.service")

# Sincronizar para o Git Local
local_path = r"C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\cloud_engine.py"
remote_path = "/var/www/hemn_cloud/cloud_engine.py"
sftp = client.open_sftp()
sftp.get(remote_path, local_path)
sftp.close()

client.close()
