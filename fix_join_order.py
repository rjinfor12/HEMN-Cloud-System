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

# Reordenação de Tabelas no JOIN (Subquery-First)
patch_script = r'''
with open('/var/www/hemn_cloud/cloud_engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Refatorar o q_template para começar pelo subquery (s)
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
                    estab.cnae_fiscal AS cnae_fiscal, 
                    estab.municipio AS municipio, 
                    s.nome_socio AS nome_socio,
                    e.natureza_juridica AS natureza_juridica
                FROM (
                    SELECT cnpj_basico, {lookup_col} AS lookup_key, nome_socio
                    FROM hemn.socios
                    WHERE {lookup_col} IN %(keys)s
                ) AS s
                INNER JOIN hemn.empresas AS e ON s.cnpj_basico = e.cnpj_basico
                INNER JOIN hemn.estabelecimento AS estab ON s.cnpj_basico = estab.cnpj_basico
                LEFT JOIN hemn.municipio AS mun ON estab.municipio = mun.municipio_codigo -- Ajustado para ser mais seguro
                ORDER BY (estab.situacao_cadastral = '02') DESC
                SETTINGS max_query_size = 31457280, join_algorithm = 'auto'"""

# Como a estrutura mudou muito, vou usar um regex para substituir o bloco q_template
import re
pattern = r'q_template = """\s+SELECT.*?SETTINGS .*?"""'
content = re.sub(pattern, f'q_template = """{new_q_template}"""', content, flags=re.DOTALL)

# Tambem ajustar o JOIN de municipio para mun.codigo (que é o padrão da nossa base)
content = content.replace("mun.municipio_codigo", "mun.codigo")

with open('/var/www/hemn_cloud/cloud_engine.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("q_template reordenado (Subquery-First) aplicado.")
'''

sftp = client.open_sftp()
with sftp.open('/tmp/fix_join_order.py', 'w') as f:
    f.write(patch_script)
sftp.close()

print(run("/var/www/hemn_cloud/venv/bin/python3 /tmp/fix_join_order.py 2>&1"))

# Reiniciar
run("systemctl restart hemn_cloud.service")

# Sincronizar para o Git Local
local_path = r"C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\cloud_engine.py"
remote_path = "/var/www/hemn_cloud/cloud_engine.py"
sftp = client.open_sftp()
sftp.get(remote_path, local_path)
sftp.close()

client.close()
