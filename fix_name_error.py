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

# Restauração de Variáveis search_names / search_terms
patch_script = r'''
with open('/var/www/hemn_cloud/cloud_engine.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Localizar onde a Phase 1.1 começa agora (depois da minha substituição por line numbers)
# Provavelmente na linha 581 ou próximo
new_logic_start = -1
for i, line in enumerate(lines):
    if "# --- PHASE 1.1: BUSCA DE CNPJs" in line:
        new_logic_start = i
        break

if new_logic_start != -1:
    # Inserir a definição das variáveis ANTES da Phase 1.1
    # Precisamos de valid_cpfs, valid_masks e all_names (que já devem existir de cima)
    definitions = [
        "            # Definições restauradas para o motor Broken-Down\n",
        "            valid_cpfs = [str(c).strip().zfill(11) for c in df_in.get('titanium_cpf', []) if str(c).strip() and str(c).upper() != 'NAN']\n",
        "            valid_masks = [f\"***{cpf[3:9]}**\" for cpf in valid_cpfs if len(cpf) >= 11]\n",
        "            search_terms = list(set(valid_cpfs + valid_masks))\n",
        "            \n",
        "            all_names = df_in.get('titanium_nome', [])\n",
        "            valid_names = [normalize_name(n) for n in all_names if n and len(str(n)) > 3]\n",
        "            search_names = list(set(valid_names))\n",
        "\n"
    ]
    final_lines = lines[:new_logic_start] + definitions + lines[new_logic_start:]
    
    with open('/var/www/hemn_cloud/cloud_engine.py', 'w', encoding='utf-8') as f:
        f.writelines(final_lines)
    print("Variáveis search_names/search_terms restauradas com sucesso.")
else:
    print("ERRO: Nao encontrei o bloco PHASE 1.1 para inserir as definições.")
'''

sftp = client.open_sftp()
with sftp.open('/tmp/fix_name_error_residual.py', 'w') as f:
    f.write(patch_script)
sftp.close()

print(run("/var/www/hemn_cloud/venv/bin/python3 /tmp/fix_name_error_residual.py 2>&1"))

# Reiniciar
run("systemctl restart hemn_cloud.service")

# Sincronizar para o Git Local
local_path = r"C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\cloud_engine.py"
remote_path = "/var/www/hemn_cloud/cloud_engine.py"
sftp = client.open_sftp()
sftp.get(remote_path, local_path)
sftp.close()

client.close()
