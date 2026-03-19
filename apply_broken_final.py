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

# Aplicação por Intervalo de Linhas
patch_script = r'''
with open('/var/www/hemn_cloud/cloud_engine.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_logic = [
    "            # --- PHASE 1.1: BUSCA DE CNPJs (Mapeamento Rápido) ---\n",
    "            found_mappings = {} # {lookup_key: [{'cnpj_basico': ...}]}\n",
    "            if search_terms:\n",
    "                q_soc = f\"SELECT cnpj_cpf_socio AS lookup_key, cnpj_basico, nome_socio FROM hemn.socios WHERE cnpj_cpf_socio IN %(keys)s\"\n",
    "                res_soc, _ = self._batch_query(q_soc, 'keys', search_terms, batch_size=20000, tid=tid, base_prog=10, max_prog=25, msg_prefix='Localizando CPFs')\n",
    "                for r_soc in res_soc:\n",
    "                    k_soc, c_soc, n_soc = r_soc\n",
    "                    if k_soc not in found_mappings: found_mappings[k_soc] = []\n",
    "                    found_mappings[k_soc].append({'cnpj_basico': c_soc, 'nome_socio': n_soc})\n",
    "            if search_names:\n",
    "                q_nm = f\"SELECT nome_socio AS lookup_key, cnpj_basico, nome_socio FROM hemn.socios WHERE nome_socio IN %(keys)s\"\n",
    "                res_nm, _ = self._batch_query(q_nm, 'keys', search_names, batch_size=20000, tid=tid, base_prog=25, max_prog=40, msg_prefix='Localizando Nomes')\n",
    "                for r_nm in res_nm:\n",
    "                    k_nm, c_nm, n_nm = r_nm\n",
    "                    if k_nm not in found_mappings: found_mappings[k_nm] = []\n",
    "                    found_mappings[k_nm].append({'cnpj_basico': c_nm, 'nome_socio': n_nm})\n",
    "            all_cnpjs = list(set([it_c['cnpj_basico'] for sl in found_mappings.values() for it_c in sl]))\n",
    "            temp_cache_estab = {}; temp_cache_emp = {}\n",
    "            if all_cnpjs:\n",
    "                self._update_task(tid, progress=45, message=f'Buscando detalhes de {len(all_cnpjs):,} empresas...')\n",
    "                q_es = \"\"\"SELECT estab.cnpj_basico, estab.cnpj_ordem, estab.cnpj_dv, estab.situacao_cadastral, estab.uf, mun.descricao AS municipio_nome, estab.ddd1, estab.telefone1, estab.ddd2, estab.telefone2, estab.correio_eletronico, estab.tipo_logradouro, estab.logradouro, estab.numero, estab.complemento, estab.bairro, estab.cep, estab.cnae_fiscal, estab.municipio FROM hemn.estabelecimento AS estab LEFT JOIN hemn.municipio AS mun ON estab.municipio = mun.codigo WHERE estab.cnpj_basico IN %(keys)s SETTINGS max_query_size = 31457280\"\"\"\n",
    "                res_es, cols_es = self._batch_query(q_es, 'keys', all_cnpjs, batch_size=10000, tid=tid, base_prog=45, max_prog=60, msg_prefix='Dados Cadastrais')\n",
    "                for r_es in res_es: d_es = dict(zip(cols_es, r_es)); c_es = d_es['cnpj_basico']\n",
    "                if c_es not in temp_cache_estab: temp_cache_estab[c_es] = []\n",
    "                temp_cache_estab[c_es].append(d_es)\n",
    "                q_em = \"SELECT cnpj_basico, razao_social, natureza_juridica FROM hemn.empresas WHERE cnpj_basico IN %(keys)s SETTINGS max_query_size = 31457280\"\n",
    "                res_em, cols_em = self._batch_query(q_em, 'keys', all_cnpjs, batch_size=10000, tid=tid, base_prog=60, max_prog=75, msg_prefix='Razão Social')\n",
    "                for r_em in res_em: d_em = dict(zip(cols_em, r_em)); temp_cache_emp[d_em['cnpj_basico']] = d_em\n",
    "            for k_gc, items_gc in found_mappings.items():\n",
    "                for it_gc in items_gc: \n",
    "                    c_gc = it_gc['cnpj_basico']; estabs_gc = temp_cache_estab.get(c_gc, []); emp_d_gc = temp_cache_emp.get(c_gc, {})\n",
    "                    for es_gc in estabs_gc:\n",
    "                        full_d_gc = {**es_gc, **emp_d_gc, 'nome_socio': it_gc['nome_socio'], 'lookup_key': k_gc}\n",
    "                        if k_gc not in global_cache: global_cache[k_gc] = []\n",
    "                        global_cache[k_gc].append(full_d_gc)\n"
]

# Substituir das linhas 581 a 717 (Indexação 0-based: 580 a 717)
final_lines = lines[:580] + new_logic + lines[717:]

with open('/var/www/hemn_cloud/cloud_engine.py', 'w', encoding='utf-8') as f:
    f.writelines(final_lines)
print("Motor Broken-Down aplicado com sucesso.")
'''

sftp = client.open_sftp()
with sftp.open('/tmp/apply_broken_down_final.py', 'w') as f:
    f.write(patch_script)
sftp.close()

print(run("/var/www/hemn_cloud/venv/bin/python3 /tmp/apply_broken_down_final.py 2>&1"))

# Reiniciar
run("systemctl restart hemn_cloud.service")

# Sincronizar para o Git Local
local_path = r"C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\cloud_engine.py"
remote_path = "/var/www/hemn_cloud/cloud_engine.py"
sftp = client.open_sftp()
sftp.get(remote_path, local_path)
sftp.close()

client.close()
