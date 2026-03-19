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

# Reescrevendo o _run_enrich para usar buscas decompostas rápidas
patch_script = r'''
import re

with open('/var/www/hemn_cloud/cloud_engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Redefinir as queries para serem simples (Single Table)
new_q_socio = """
    SELECT {lookup_col} AS lookup_key, cnpj_basico, nome_socio 
    FROM hemn.socios 
    WHERE {lookup_col} IN %(keys)s
    SETTINGS max_query_size = 31457280
"""

new_q_estab = """
    SELECT 
        estab.cnpj_basico AS lookup_key, estab.cnpj_basico AS cnpj_basico, 
        estab.cnpj_ordem AS cnpj_ordem, estab.cnpj_dv AS cnpj_dv, estab.situacao_cadastral AS situacao_cadastral, 
        estab.uf AS uf, mun.descricao AS municipio_nome, estab.ddd1 AS ddd1, estab.telefone1 AS telefone1, 
        estab.ddd2 AS ddd2, estab.telefone2 AS telefone2, estab.correio_eletronico AS correio_eletronico, 
        estab.tipo_logradouro AS tipo_logradouro, estab.logradouro AS logradouro, estab.numero AS numero, 
        estab.complemento AS complemento, estab.bairro AS bairro, estab.cep AS cep, 
        estab.cnae_fiscal AS cnae_fiscal, estab.municipio AS municipio
    FROM hemn.estabelecimento AS estab
    LEFT JOIN hemn.municipio AS mun ON estab.municipio = mun.codigo
    WHERE estab.cnpj_basico IN %(keys)s
    SETTINGS max_query_size = 31457280
"""

new_q_empresa = """
    SELECT cnpj_basico AS lookup_key, razao_social, natureza_juridica
    FROM hemn.empresas
    WHERE cnpj_basico IN %(keys)s
    SETTINGS max_query_size = 31457280
"""

# Substituir todo o fluxo de Fase 1.1 e 1.2
# Vamos simplificar drasticamente o _run_enrich

# Localizar o ponto de início (PHASE 1.1: SOCIO LOOKUP)
# E o ponto de fim antes da PHASE 2

start_token = "# --- PHASE 1.1: SOCIO LOOKUP"
end_token = "# --- PHASE 1.3: INTELIGÊNCIA RESIDUAL"

new_workflow = r"""
            # --- PHASE 1.1: BUSCA DE CNPJs (Mapeamento Rápido) ---
            found_mappings = {} # {lookup_key: [cnpj_basico, ...]}
            
            # 1.1.1: Buscar por CPF/Máscara
            if search_terms:
                q = f"SELECT cnpj_cpf_socio AS lookup_key, cnpj_basico, nome_socio FROM hemn.socios WHERE cnpj_cpf_socio IN %(keys)s"
                res, _ = self._batch_query(q, "keys", search_terms, batch_size=20000, tid=tid, base_prog=10, max_prog=25, msg_prefix="Localizando CPFs")
                for r in res:
                    k, c, n = r
                    if k not in found_mappings: found_mappings[k] = []
                    found_mappings[k].append({'cnpj_basico': c, 'nome_socio': n})
            
            # 1.1.2: Buscar por Nome
            if search_names:
                q = f"SELECT nome_socio AS lookup_key, cnpj_basico, nome_socio FROM hemn.socios WHERE nome_socio IN %(keys)s"
                res, _ = self._batch_query(q, "keys", search_names, batch_size=20000, tid=tid, base_prog=25, max_prog=40, msg_prefix="Localizando Nomes")
                for r in res:
                    k, c, n = r
                    if k not in found_mappings: found_mappings[k] = []
                    found_mappings[k].append({'cnpj_basico': c, 'nome_socio': n})

            all_cnpjs = list(set([item['cnpj_basico'] for sublist in found_mappings.values() for item in sublist]))
            
            # --- PHASE 1.2: BUSCA DE DETALHES (Estabeleximentos e Empresas) ---
            # Vamos buscar os detalhes apenas para os CNPJs encontrados
            temp_cache_estab = {}
            temp_cache_emp = {}
            
            if all_cnpjs:
                self._update_task(tid, progress=45, message=f"Buscando detalhes de {len(all_cnpjs):,} empresas...")
                # Estabelecimentos
                q_estab = """ + "\"" + "\"" + "\"" + """
                    SELECT estab.cnpj_basico, estab.cnpj_ordem, estab.cnpj_dv, estab.situacao_cadastral, 
                           estab.uf, mun.descricao AS municipio_nome, estab.ddd1, estab.telefone1, 
                           estab.ddd2, estab.telefone2, estab.correio_eletronico, 
                           estab.tipo_logradouro, estab.logradouro, estab.numero, estab.complemento, 
                           estab.bairro, estab.cep, estab.cnae_fiscal, estab.municipio
                    FROM hemn.estabelecimento AS estab
                    LEFT JOIN hemn.municipio AS mun ON estab.municipio = mun.codigo
                    WHERE estab.cnpj_basico IN %(keys)s
                    SETTINGS max_query_size = 31457280
                """ + "\"" + "\"" + "\"" + """
                res_estab, cols_estab = self._batch_query(q_estab, "keys", all_cnpjs, batch_size=10000, tid=tid, base_prog=45, max_prog=60, msg_prefix="Dados Cadastrais")
                for r in res_estab:
                    d = dict(zip(cols_estab, r))
                    c = d['cnpj_basico']
                    if c not in temp_cache_estab: temp_cache_estab[c] = []
                    temp_cache_estab[c].append(d)
                
                # Empresas
                q_emp = "SELECT cnpj_basico, razao_social, natureza_juridica FROM hemn.empresas WHERE cnpj_basico IN %(keys)s SETTINGS max_query_size = 31457280"
                res_emp, cols_emp = self._batch_query(q_emp, "keys", all_cnpjs, batch_size=10000, tid=tid, base_prog=60, max_prog=75, msg_prefix="Razão Social")
                for r in res_emp:
                    d = dict(zip(cols_emp, r))
                    temp_cache_emp[d['cnpj_basico']] = d

            # Montar o global_cache
            for k, items in found_mappings.items():
                for it in items:
                    c = it['cnpj_basico']
                    estabs = temp_cache_estab.get(c, [])
                    emp_data = temp_cache_emp.get(c, {})
                    for es in estabs:
                        full_d = {**es, **emp_data, 'nome_socio': it['nome_socio'], 'lookup_key': k}
                        if k not in global_cache: global_cache[k] = []
                        global_cache[k].append(full_d)
"""

# Substituir o bloco
# pattern = re.escape(start_token) + ".*?" + re.escape(end_token) # Nao funciona bem por causa do DOTALL
# Vou usar uma abordagem por índices de string
idx_start = content.find(start_token)
idx_end = content.find(end_token)

if idx_start != -1 and idx_end != -1:
    content = content[:idx_start] + new_workflow + content[idx_end:]
    print("Workflow Decomposto aplicado com sucesso.")
else:
    print(f"ERRO: Nao encontrei os tokens (Start: {idx_start}, End: {idx_end})")

with open('/var/www/hemn_cloud/cloud_engine.py', 'w', encoding='utf-8') as f:
    f.write(content)
'''

sftp = client.open_sftp()
with sftp.open('/tmp/rewrite_broken_down_join.py', 'w') as f:
    f.write(patch_script)
sftp.close()

print(run("/var/www/hemn_cloud/venv/bin/python3 /tmp/rewrite_broken_down_join.py 2>&1"))

# Reiniciar
run("systemctl restart hemn_cloud.service")

# Sincronizar para o Git Local
local_path = r"C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\cloud_engine.py"
remote_path = "/var/www/hemn_cloud/cloud_engine.py"
sftp = client.open_sftp()
sftp.get(remote_path, local_path)
sftp.close()

client.close()
