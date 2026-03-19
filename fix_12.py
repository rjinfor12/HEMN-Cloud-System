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

# Remoção garantida do bloco de 12% e 15%
patch_script = r'''
import re

with open('/var/www/hemn_cloud/cloud_engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Vamos remover o bloco que vai de "# --- PHASE 1.2: MEI DIRECT LOOKUP" ate "found_mei_basics = list(set(found_mei_basics))"
# e também o que adiciona basics ao search_terms
pattern = r"            # --- PHASE 1.2: MEI DIRECT LOOKUP.*?search_terms = list\(set\(search_terms\)\)"
content = re.sub(pattern, "            # [BLOCO_ANTIGO_REMOVIDO]", content, flags=re.DOTALL)

with open('/var/www/hemn_cloud/cloud_engine.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Bloco de 12% removido com sucesso.")
'''

sftp = client.open_sftp()
with sftp.open('/tmp/fix_12_percent.py', 'w') as f:
    f.write(patch_script)
sftp.close()

print(run("/var/www/hemn_cloud/venv/bin/python3 /tmp/fix_12_percent.py 2>&1"))

# Reiniciar
run("systemctl restart hemn_cloud.service")

# Sincronizar para o Git Local
local_path = r"C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\cloud_engine.py"
remote_path = "/var/www/hemn_cloud/cloud_engine.py"
sftp = client.open_sftp()
sftp.get(remote_path, local_path)
sftp.close()

client.close()
