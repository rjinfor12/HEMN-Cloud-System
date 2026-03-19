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

# Correção Definitiva de Sintaxe
patch_script = r'''
with open('/var/www/hemn_cloud/cloud_engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Substituir a cláusula LEFT JOIN inteira para garantir consistência
old_line = "LEFT JOIN hemn.municipio AS mun ON estab.municipio = m.codigo"
new_line = "LEFT JOIN hemn.municipio AS mun ON estab.municipio = mun.codigo"

content = content.replace(old_line, new_line)

with open('/var/www/hemn_cloud/cloud_engine.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Sintaxe SQL corrigida (m.codigo -> mun.codigo).")
'''

sftp = client.open_sftp()
with sftp.open('/tmp/fix_final_sql.py', 'w') as f:
    f.write(patch_script)
sftp.close()

print(run("/var/www/hemn_cloud/venv/bin/python3 /tmp/fix_final_sql.py 2>&1"))

# Reiniciar
run("systemctl restart hemn_cloud.service")

# Sincronizar para o Git Local
local_path = r"C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\cloud_engine.py"
remote_path = "/var/www/hemn_cloud/cloud_engine.py"
sftp = client.open_sftp()
sftp.get(remote_path, local_path)
sftp.close()

client.close()
