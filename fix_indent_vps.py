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

# Correção Total de Indentação
patch_script = r'''
with open('/var/www/hemn_cloud/cloud_engine.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Vamos reconstruir o trecho problematico (aproximadamente entre 804 e 820)
# Vamos usar busca por texto para garantir
new_lines = []
for line in lines:
    if "Concatenar Nome + CPF conforme solicitado" in line:
        # Pular as proximas linhas ate row_dict['RAZAO_SOCIAL'] se ja estiverem la bagunçadas
        continue
    if "s_nome =" in line or "s_cpf =" in line or "if not s_nome" in line or "s_nome = re.sub" in line or "s_cpf = \"\".join" in line:
        continue
    if "row_dict['SÓCIO_IDENTIFICADO'] =" in line:
        continue
    
    # Reparar a linha row_dict['RAZAO_SOCIAL'] que perdou indentacao
    if line.startswith("row_dict['RAZAO_SOCIAL']"):
        # Reinserir o bloco inteiro com indentacao correta (16 espaços)
        indent = "                "
        new_lines.append(f"{indent}# Concatenar Nome + CPF conforme solicitado pelo Usuário\n")
        new_lines.append(f"{indent}s_nome = str(best_match.get('nome_socio', '')).strip()\n")
        new_lines.append(f"{indent}s_cpf = str(best_match.get('cnpj_cpf_socio', '')).strip()\n")
        new_lines.append(f"{indent}if not s_nome and best_match.get('natureza_juridica') == '2135':\n")
        new_lines.append(f"{indent}    # Para MEI, extraímos o nome da Razão Social\n")
        new_lines.append(f"{indent}    s_nome = re.sub(r'^\\d{{2}}\\.\\d{{3}}\\.\\d{{3}}\\s+', '', best_match.get('razao_social', ''))\n")
        new_lines.append(f"{indent}    s_nome = re.sub(r'\\s+\\d{{11}}$', '', s_nome).strip()\n")
        new_lines.append(f"{indent}    s_cpf = \"\".join(re.findall(r'\\d{{11}}$', best_match.get('razao_social', '')))\n")
        new_lines.append(f"\n")
        new_lines.append(f"{indent}row_dict['SÓCIO_IDENTIFICADO'] = f\"{{s_nome}} - {{s_cpf}}\".strip(\" -\")\n")
        new_lines.append(f"{indent}row_dict['RAZAO_SOCIAL'] = best_match['razao_social']\n")
    else:
        new_lines.append(line)

with open('/var/www/hemn_cloud/cloud_engine.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print("Indentaçao corrigida e código restaurado.")
'''

sftp = client.open_sftp()
with sftp.open('/tmp/fix_indentation_final.py', 'w') as f:
    f.write(patch_script)
sftp.close()

print(run("/var/www/hemn_cloud/venv/bin/python3 /tmp/fix_indentation_final.py 2>&1"))

# Reiniciar
run("systemctl restart hemn_cloud.service")

# Sincronizar para o Git Local
local_path = r"C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\cloud_engine.py"
remote_path = "/var/www/hemn_cloud/cloud_engine.py"
sftp = client.open_sftp()
sftp.get(remote_path, local_path)
sftp.close()

client.close()
