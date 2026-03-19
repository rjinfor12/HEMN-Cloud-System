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

# Restauração de global_cache
patch_script = r'''
with open('/var/www/hemn_cloud/cloud_engine.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_logic_start = -1
for i, line in enumerate(lines):
    if "# --- PHASE 1.1: BUSCA DE CNPJs" in line:
        new_logic_start = i
        break

if new_logic_start != -1:
    # Inserir global_cache anes da Phase 1.1
    # Vou aproveitar e colocar todas as iniciais para nao ter mais erro
    definitions = [
        "            global_cache = {} # Inicialização crítica\n",
        "\n"
    ]
    # Verificar se ja nao existe acima
    already_has = False
    for j in range(max(0, new_logic_start - 20), new_logic_start):
        if "global_cache =" in lines[j]:
            already_has = True
            break
    
    if not already_has:
        final_lines = lines[:new_logic_start] + definitions + lines[new_logic_start:]
        with open('/var/www/hemn_cloud/cloud_engine.py', 'w', encoding='utf-8') as f:
            f.writelines(final_lines)
        print("global_cache restaurado com sucesso.")
    else:
        print("global_cache já existe acima do bloco.")
else:
    print("ERRO: Nao encontrei o bloco PHASE 1.1.")
'''

sftp = client.open_sftp()
with sftp.open('/tmp/fix_global_cache_residual.py', 'w') as f:
    f.write(patch_script)
sftp.close()

print(run("/var/www/hemn_cloud/venv/bin/python3 /tmp/fix_global_cache_residual.py 2>&1"))

# Reiniciar
run("systemctl restart hemn_cloud.service")

# Sincronizar para o Git Local
local_path = r"C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\cloud_engine.py"
remote_path = "/var/www/hemn_cloud/cloud_engine.py"
sftp = client.open_sftp()
sftp.get(remote_path, local_path)
sftp.close()

client.close()
