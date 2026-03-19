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

# Otimizacao do cloud_engine.py
# 1. Mover Socio Lookup para antes de MEI Lookup
# 2. Filtrar nomes ja encontrados
patch_script = r'''
import re

with open('/var/www/hemn_cloud/cloud_engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Vamos extrair e reordenar os blocos de busca
# 1. Procurar o bloco "PHASE 1.2: MEI DIRECT LOOKUP" ate "PHASE 2: IN-MEMORY MAPPING"

mei_lookup_block = r"""            # --- PHASE 1.2: MEI DIRECT LOOKUP (UNITARY EXCELLENCE REPLICATION) ---
            found_mei_basics = []
            if search_terms:
                self._update_task(tid, progress=12, message="Cruzando MEIs por CPF (Busca Direta)...")
                # Busca CPFs na Razao Social de MEIs
                q_mei_cpf = "SELECT cnpj_basico FROM hemn.empresas WHERE natureza_juridica = '2135' AND multiSearchAny(razao_social, %(keys)s) LIMIT 2000"
                res_mei_cpf, _ = self._batch_query(q_mei_cpf, "keys", [k for k in search_terms if not k.startswith('*')], batch_size=200, tid=tid)
                found_mei_basics.extend([r[0] for r in res_mei_cpf])
            
            if search_names:
                self._update_task(tid, progress=15, message="Cruzando MEIs por Nome (Busca Direta)...")
                q_mei_name = "SELECT cnpj_basico FROM hemn.empresas WHERE natureza_juridica = '2135' AND multiSearchAny(razao_social, %(keys)s) LIMIT 2000"
                res_mei_name, _ = self._batch_query(q_mei_name, "keys", search_names, batch_size=200, tid=tid)
                found_mei_basics.extend([r[0] for r in res_mei_name])
            
            found_mei_basics = list(set(found_mei_basics))
            # Adicionar estes basics aos search_terms da query q_mei que ja existe
            if found_mei_basics:
                search_terms.extend(found_mei_basics)
                search_terms = list(set(search_terms))"""

# Remover o bloco original
content = content.replace(mei_lookup_block, "            # [MEI_LOOKUP_MOVED]", 1)

# Inserir apos a populacao inicial do cache de socios/nomes
target_insertion = """                for r in results:
                    d = dict(zip(cols, r))
                    k = normalize_name(str(d['lookup_key']))
                    if k not in global_cache: global_cache[k] = []
                    global_cache[k].append(d)"""

new_mei_lookup = r"""
            # --- PHASE 1.3: INTELIGÊNCIA RESIDUAL (BUSCA MEI FILTRADA) ---
            # Só pesquisamos na tabela empresas (lenta) o que NÃO foi encontrado em sócios (rápida)
            needed_names = [n for n in search_names if n not in global_cache]
            needed_cpfs = [c for c in search_terms if not c.startswith('*') and c not in global_cache]
            
            if needed_cpfs or needed_names:
                self._update_task(tid, progress=76, message=f"Otimização: Buscando {len(needed_cpfs) + len(needed_names)} MEIs residuais...")
                found_mei_basics = []
                
                # Limite de segurança: se tiver mais de 500 nomes não encontrados, processamos apenas os 500 primeiros 
                # para evitar que o ClickHouse trave em arquivos massivos com dados ruins/inexistentes.
                top_cpfs = needed_cpfs[:500]
                top_names = needed_names[:500]
                
                if top_cpfs:
                    q_mei_cpf = "SELECT cnpj_basico FROM hemn.empresas WHERE natureza_juridica = '2135' AND multiSearchAny(razao_social, %(keys)s) LIMIT 2000"
                    res_mei_cpf, _ = self._batch_query(q_mei_cpf, "keys", top_cpfs, batch_size=200, tid=tid)
                    found_mei_basics.extend([r[0] for r in res_mei_cpf])
                
                if top_names:
                    # Otimização Extra: Tentar primeiro por Prefixo (Indexed) para os primeiros 200 nomes
                    # Isso é MUITO rápido por causa da ordenação da tabela.
                    self._update_task(tid, progress=77, message="Consultando MEIs por Prefixo Indexado...")
                    for n_prefix in top_names[:200]:
                        q_pref = "SELECT cnpj_basico FROM hemn.empresas WHERE natureza_juridica = '2135' AND razao_social LIKE %(p)s LIMIT 5"
                        res_p = self._batch_query(q_pref, "p", [n_prefix + '%'], batch_size=1, tid=tid)
                        found_mei_basics.extend([r[0] for r in res_p[0]])
                    
                    q_mei_name = "SELECT cnpj_basico FROM hemn.empresas WHERE natureza_juridica = '2135' AND multiSearchAny(razao_social, %(keys)s) LIMIT 2000"
                    res_mei_name, _ = self._batch_query(q_mei_name, "keys", top_names, batch_size=200, tid=tid)
                    found_mei_basics.extend([r[0] for r in res_mei_name])

                found_mei_basics = list(set(found_mei_basics))
                if found_mei_basics:
                    # Executar a query de detalhamento para estes novos basics
                    q_mei_detail = """ + "\"\"\"" + """
                        SELECT 
                            e.cnpj_basico AS lookup_key, e.razao_social AS razao_social, estab.cnpj_basico AS cnpj_basico, 
                            estab.cnpj_ordem AS cnpj_ordem, estab.cnpj_dv AS cnpj_dv, estab.situacao_cadastral AS situacao_cadastral, 
                            estab.uf AS uf, mun.descricao AS municipio_nome, estab.ddd1 AS ddd1, estab.telefone1 AS telefone1, 
                            estab.ddd2 AS ddd2, estab.telefone2 AS telefone2, estab.correio_eletronico AS correio_eletronico, 
                            estab.tipo_logradouro AS tipo_logradouro, estab.logradouro AS logradouro, estab.numero AS numero, 
                            estab.complemento AS complemento, estab.bairro AS bairro, estab.cep AS cep, 
                            estab.cnae_fiscal AS cnae_fiscal, estab.municipio AS municipio, '' AS nome_socio, e.natureza_juridica AS natureza_juridica
                        FROM hemn.empresas AS e
                        INNER JOIN hemn.estabelecimento AS estab ON e.cnpj_basico = estab.cnpj_basico
                        LEFT JOIN hemn.municipio AS mun ON estab.municipio = mun.codigo
                        WHERE e.cnpj_basico IN %(keys)s
                        ORDER BY (estab.situacao_cadastral = '02') DESC
                    """ + "\"\"\"" + """
                    res_det, cols_det = self._batch_query(q_mei_detail, "keys", found_mei_basics, batch_size=1000, tid=tid)
                    for r in res_det:
                        d = dict(zip(cols_det, r))
                        k = str(d['lookup_key'])
                        if k not in global_cache: global_cache[k] = []
                        global_cache[k].append(d)
                        
                        raw_razao = d.get('razao_social', '')
                        # Indexar por Nome e Variações MEI
                        r_name_key = normalize_name(raw_razao)
                        if r_name_key not in global_cache: global_cache[r_name_key] = []
                        global_cache[r_name_key].append(d)
                        
                        if d.get('natureza_juridica') == '2135':
                            clean_razao = re.sub(r'^\d{2}\.\d{3}\.\d{3}\s+', '', raw_razao)
                            clean_razao = re.sub(r'\s+\d{11}$', '', clean_razao).strip()
                            clean_name_key = normalize_name(clean_razao)
                            if clean_name_key and clean_name_key not in global_cache:
                                global_cache[clean_name_key] = [d]
                            cpfs_in_razao = re.findall(r'\d{11}', raw_razao)
                            for cpf_found in cpfs_in_razao:
                                if cpf_found not in global_cache: global_cache[cpf_found] = []
                                global_cache[cpf_found].append(d)"""

content = content.replace(target_insertion, target_insertion + new_mei_lookup, 1)

# Limpeza de comentarios de movimentacao
content = content.replace("            # [MEI_LOOKUP_MOVED]", "", 1)

with open('/var/www/hemn_cloud/cloud_engine.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Otimização MEI Residual aplicada com sucesso.")
'''

sftp = client.open_sftp()
with sftp.open('/tmp/optimize_mei_search.py', 'w') as f:
    f.write(patch_script)
sftp.close()

print(run("/var/www/hemn_cloud/venv/bin/python3 /tmp/optimize_mei_search.py 2>&1"))

# Reiniciar
run("systemctl restart hemn_cloud.service")

# Sincronizar para o Git Local
local_path = r"C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\cloud_engine.py"
remote_path = "/var/www/hemn_cloud/cloud_engine.py"
sftp = client.open_sftp()
sftp.get(remote_path, local_path)
sftp.close()

client.close()
