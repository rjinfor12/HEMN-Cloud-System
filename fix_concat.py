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

# Adição de Concatenação Nome + CPF
patch_script = r'''
import re

with open('/var/www/hemn_cloud/cloud_engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Atualizar Phase 1.1 para trazer o CPF/Mascara do Socio
content = content.replace(
    "SELECT cnpj_cpf_socio AS lookup_key, cnpj_basico, nome_socio FROM hemn.socios",
    "SELECT cnpj_cpf_socio AS lookup_key, cnpj_basico, nome_socio, cnpj_cpf_socio FROM hemn.socios"
)
content = content.replace(
    "SELECT nome_socio AS lookup_key, cnpj_basico, nome_socio FROM hemn.socios",
    "SELECT nome_socio AS lookup_key, cnpj_basico, nome_socio, cnpj_cpf_socio FROM hemn.socios"
)

# Atualizar mapeamento de r_soc
content = content.replace(
    "k_soc, c_soc, n_soc = r_soc",
    "k_soc, c_soc, n_soc, cpf_soc = r_soc"
)
content = content.replace(
    "found_mappings[k_soc].append({'cnpj_basico': c_soc, 'nome_socio': n_soc})",
    "found_mappings[k_soc].append({'cnpj_basico': c_soc, 'nome_socio': n_soc, 'cnpj_cpf_socio': cpf_soc})"
)

# Atualizar mapeamento de r_nm
content = content.replace(
    "k_nm, c_nm, n_nm = r_nm",
    "k_nm, c_nm, n_nm, cpf_nm = r_nm"
)
content = content.replace(
    "found_mappings[k_nm].append({'cnpj_basico': c_nm, 'nome_socio': n_nm})",
    "found_mappings[k_nm].append({'cnpj_basico': c_nm, 'nome_socio': n_nm, 'cnpj_cpf_socio': cpf_nm})"
)

# 2. Injetar cnpj_cpf_socio no full_d_gc (Final do Mapeamento Phase 1.2)
content = content.replace(
    "full_d_gc = {**es_gc, **emp_d_gc, 'nome_socio': it_gc['nome_socio'], 'lookup_key': k_gc}",
    "full_d_gc = {**es_gc, **emp_d_gc, 'nome_socio': it_gc['nome_socio'], 'cnpj_cpf_socio': it_gc.get('cnpj_cpf_socio', ''), 'lookup_key': k_gc}"
)

# 3. Criar a coluna concatenada na Phase 2
target_injection = "row_dict['RAZAO_SOCIAL'] = best_match['razao_social']"
new_col = """                # Concatenar Nome + CPF conforme solicitado pelo Usuário
                s_nome = str(best_match.get('nome_socio', '')).strip()
                s_cpf = str(best_match.get('cnpj_cpf_socio', '')).strip()
                if not s_nome and best_match.get('natureza_juridica') == '2135':
                    # Para MEI, extraímos o nome da Razão Social
                    s_nome = re.sub(r'^\d{2}\.\d{3}\.\d{3}\s+', '', best_match.get('razao_social', ''))
                    s_nome = re.sub(r'\s+\d{11}$', '', s_nome).strip()
                    s_cpf = "".join(re.findall(r'\d{11}$', best_match.get('razao_social', '')))
                
                row_dict['SÓCIO_IDENTIFICADO'] = f"{s_nome} - {s_cpf}".strip(" -")"""

content = content.replace(target_injection, new_col + "\n" + target_injection)

# 4. Adicionar à lista de colunas finais
content = content.replace(
    "final_columns = ['CNPJ', 'NOME DA EMPRESA',",
    "final_columns = ['CNPJ', 'NOME DA EMPRESA', 'SÓCIO_IDENTIFICADO',"
)

with open('/var/www/hemn_cloud/cloud_engine.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Concatenação Nome + CPF aplicada com sucesso.")
'''

sftp = client.open_sftp()
with sftp.open('/tmp/concatenate_name_cpf.py', 'w') as f:
    f.write(patch_script)
sftp.close()

print(run("/var/www/hemn_cloud/venv/bin/python3 /tmp/concatenate_name_cpf.py 2>&1"))

# Reiniciar
run("systemctl restart hemn_cloud.service")

# Sincronizar para o Git Local
local_path = r"C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\cloud_engine.py"
remote_path = "/var/www/hemn_cloud/cloud_engine.py"
sftp = client.open_sftp()
sftp.get(remote_path, local_path)
sftp.close()

client.close()
