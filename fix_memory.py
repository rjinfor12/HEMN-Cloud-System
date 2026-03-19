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

# Refatoração Final do SQL para Alta Performance e Baixo Consumo de Memória
patch_script = r'''
with open('/var/www/hemn_cloud/cloud_engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Ajustar batch_size para 5000 (Seguro e Rápido)
content = content.replace("batch_size=20000", "batch_size=5000")

# 2. Refatorar q_template: Subconsulta filtrada no RIGHT side (EXTREME EFFICIENCY)
old_q_template = """                SELECT 
                    s.{lookup_col} AS lookup_key,
                    e.razao_social AS razao_social, 
                    estab.cnpj_basico AS cnpj_basico, 
                    estab.cnpj_ordem AS cnpj_ordem, 
                    estab.cnpj_dv AS cnpj_dv, 
                    estab.situacao_cadastral AS situacao_cadastral, 
                    estab.uf AS uf, 
                    mun.descricao AS municipio_nome, 
                    estab.ddd1 AS ddd1, 
                    estab.telefone1 AS telefone1, 
                    estab.ddd2 AS ddd2, 
                    estab.telefone2 AS telefone2, 
                    estab.correio_eletronico AS correio_eletronico, 
                    estab.tipo_logradouro AS tipo_logradouro, 
                    estab.logradouro AS logradouro, 
                    estab.numero AS numero, 
                    estab.complemento AS complemento, 
                    estab.bairro AS bairro, 
                    estab.cep AS cep, 
                    estab.cnae_fiscal AS cnae_fiscal, 
                    estab.municipio AS municipio, 
                    s.nome_socio AS nome_socio,
                    e.natureza_juridica AS natureza_juridica
                FROM hemn.socios AS s
                INNER JOIN hemn.empresas AS e ON s.cnpj_basico = e.cnpj_basico
                INNER JOIN hemn.estabelecimento AS estab ON e.cnpj_basico = estab.cnpj_basico
                LEFT JOIN hemn.municipio AS mun ON estab.municipio = mun.codigo
                WHERE s.{lookup_col} IN %(keys)s
                ORDER BY (estab.situacao_cadastral = '02') DESC
                SETTINGS max_query_size = 31457280, join_algorithm = 'auto'"""

new_q_template = """                SELECT 
                    s.lookup_key AS lookup_key,
                    e.razao_social AS razao_social, 
                    estab.cnpj_basico AS cnpj_basico, 
                    estab.cnpj_ordem AS cnpj_ordem, 
                    estab.cnpj_dv AS cnpj_dv, 
                    estab.situacao_cadastral AS situacao_cadastral, 
                    estab.uf AS uf, 
                    mun.descricao AS municipio_nome, 
                    estab.ddd1 AS ddd1, 
                    estab.telefone1 AS telefone1, 
                    estab.ddd2 AS ddd2, 
                    estab.telefone2 AS telefone2, 
                    estab.correio_eletronico AS correio_eletronico, 
                    estab.tipo_logradouro AS tipo_logradouro, 
                    estab.logradouro AS logradouro, 
                    estab.numero AS numero, 
                    estab.complemento AS complemento, 
                    estab.bairro AS bairro, 
                    estab.cep AS cep, 
                    estab.cnae_fiscal AS CNAE, 
                    estab.municipio AS municipio, 
                    s.nome_socio AS nome_socio,
                    e.natureza_juridica AS natureza_juridica
                FROM hemn.estabelecimento AS estab
                INNER JOIN hemn.empresas AS e ON estab.cnpj_basico = e.cnpj_basico
                INNER JOIN (
                    SELECT cnpj_basico, {lookup_col} AS lookup_key, nome_socio
                    FROM hemn.socios
                    WHERE {lookup_col} IN %(keys)s
                ) AS s ON estab.cnpj_basico = s.cnpj_basico
                LEFT JOIN hemn.municipio AS m ON estab.municipio = m.codigo
                ORDER BY (estab.situacao_cadastral = '02') DESC
                SETTINGS max_query_size = 31457280, join_algorithm = 'auto'"""

if old_q_template in content:
    content = content.replace(old_q_template, new_q_template)
    print("q_template refatorado para usar subconsulta filtrada (Memory Safe).")
else:
    print("ERRO: Nao encontrei o q_template para refatorar.")

with open('/var/www/hemn_cloud/cloud_engine.py', 'w', encoding='utf-8') as f:
    f.write(content)
'''

sftp = client.open_sftp()
with sftp.open('/tmp/fix_memory_crash.py', 'w') as f:
    f.write(patch_script)
sftp.close()

print(run("/var/www/hemn_cloud/venv/bin/python3 /tmp/fix_memory_crash.py 2>&1"))

# Reiniciar
run("systemctl restart hemn_cloud.service")

# Sincronizar para o Git Local
local_path = r"C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\cloud_engine.py"
remote_path = "/var/www/hemn_cloud/cloud_engine.py"
sftp = client.open_sftp()
sftp.get(remote_path, local_path)
sftp.close()

client.close()
