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

# Super Otimizacao para Lotes Massivos
patch_script = r'''
import re

with open('/var/www/hemn_cloud/cloud_engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Aumentar batch_size padrão e reduzir updates de task
content = content.replace("batch_size=2000, tid=None", "batch_size=10000, tid=None")
content = content.replace("batch_size=2000, tid=tid", "batch_size=10000, tid=tid")

# 2. Otimizar _batch_query para atualizar meno frequente
old_update = """            if tid and max_prog > base_prog:
                prog = base_prog + int((i / total) * (max_prog - base_prog))
                self._update_task(tid, progress=prog, message=f"{msg_prefix} ({i:,}/{total:,})...")"""

new_update = """            if tid and max_prog > base_prog:
                # Atualizar apenas a cada 20.000 registros para evitar overhead de DB no TaskStatus
                if i % 20000 == 0 or i + batch_size >= total:
                    prog = base_prog + int((i / total) * (max_prog - base_prog))
                    self._update_task(tid, progress=prog, message=f"{msg_prefix} ({i:,}/{total:,})...")"""

content = content.replace(old_update, new_update)

# 3. Otimizar Loop Phase 2 (de iterrows para dict records) - MUITO mais rápido para 156k
old_loop_start = "            for idx, row in df_in.iterrows():"
new_loop_start = """            # Otimização: Converter DataFrame para dicionários para loop 10x mais rápido
            records = df_in.to_dict('records')
            for i_idx, row in enumerate(records):
                if i_idx % 5000 == 0:
                    status = self.get_task_status(tid)
                    if status.get("status") == "CANCELLED": return
                    self._update_task(tid, progress=80 + int((i_idx/total)*15), message=f"Aplicando Inteligência ({i_idx:,}/{total:,})...")
"""
content = content.replace(old_loop_start, new_loop_start)

with open('/var/www/hemn_cloud/cloud_engine.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Super Otimização de Performance aplicada.")
'''

sftp = client.open_sftp()
with sftp.open('/tmp/super_optimize.py', 'w') as f:
    f.write(patch_script)
sftp.close()

print(run("/var/www/hemn_cloud/venv/bin/python3 /tmp/super_optimize.py 2>&1"))

# Reiniciar
run("systemctl restart hemn_cloud.service")

# Sincronizar para o Git Local
local_path = r"C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\cloud_engine.py"
remote_path = "/var/www/hemn_cloud/cloud_engine.py"
sftp = client.open_sftp()
sftp.get(remote_path, local_path)
sftp.close()

client.close()
