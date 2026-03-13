import paramiko, os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

def run(cmd):
    stdin, stdout, stderr = client.exec_command(cmd)
    stdout.channel.recv_exit_status()
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    return out + err

# Script robusto para atualizar o arquivo remotamente
update_script = r"""
import sys

path = '/var/www/hemn_cloud/cloud_engine.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Query original do backup (usada para localizar o ponto de inserção)
# Note: Usei recortes menores para evitar erros de indentação/espaçamento no replace
old_query_marker = 'q = f"""'
old_query_end = 'JOIN hemn.empresas e ON estab.cnpj_basico = e.cnpj_basico'

# Nova Query Otimizada (Ordem Invertida para Performance VPS)
new_query = '''            q = f"""
                SELECT e.razao_social as NOME_DA_EMPRESA, 
                       concat(estab.cnpj_basico, estab.cnpj_ordem, estab.cnpj_dv) as CNPJ, 
                       estab.situacao_cadastral as SITUACAO_CADASTRAL,
                       estab.cnae_fiscal as CNAE, 
                       estab.logradouro as LOGRADOURO,
                       estab.numero as NUMERO_DA_FAIXADA,
                       estab.bairro as BAIRRO,
                       estab.CIDADE, estab.uf as UF, estab.cep as CEP, 
                       estab.ddd1, estab.telefone1, estab.ddd2, estab.telefone1 as telefone1,
                       estab.ddd2 as ddd2, estab.telefone2 as telefone2 
                FROM hemn.empresas e
                JOIN (
                    SELECT estab.*, m.descricao as CIDADE 
                    FROM hemn.estabelecimento estab 
                    LEFT JOIN hemn.municipio m ON estab.municipio = m.codigo 
                    WHERE {where_clause} 
                    LIMIT 20000000
                ) as estab ON e.cnpj_basico = estab.cnpj_basico
                SETTINGS join_algorithm = 'auto', max_bytes_before_external_join = 2000000000
            """'''

# Localizar o bloco da query entre os marcadores
# Como regex pode ser perigoso com f""" complexas, vamos usar substituição de bloco se encontrarmos a assinatura
if 'FROM (' in content and 'JOIN hemn.empresas' in content:
    # Esta é uma estratégia de substituição baseada em marcos
    start_idx = content.find('q = f"""')
    end_idx = content.find('JOIN hemn.empresas e ON estab.cnpj_basico = e.cnpj_basico')
    if start_idx != -1 and end_idx != -1:
        # Pega até o final da aspas triplas
        real_end = content.find('"""', end_idx) + 3
        content = content[:start_idx] + new_query + content[real_end:]
        print("Bloco de Query Otimizado.")

# Mapeamento de Colunas (Fix de Encoding e Preenchimento)
old_cols_marker = 'final_columns = ['
new_cols_block = '''            final_columns = [
                'CNPJ', 'NOME DA EMPRESA', 'SITUAÇÃO CADASTRAL', 'CNAE', 
                'LOGRADOURO', 'NUMERO DA FAIXADA', 'BAIRRO', 'CIDADE', 
                'UF', 'CEP', 'TELEFONE SOLICITADO', 'OPERADORA DO TELEFONE'
            ]
            
            df = df.rename(columns={
                'NOME_DA_EMPRESA': 'NOME DA EMPRESA',
                'SITUACAO_CADASTRAL': 'SITUAÇÃO CADASTRAL',
                'NUMERO_DA_FAIXADA': 'NUMERO DA FAIXADA'
            })
            df = df.fillna("")'''

if old_cols_marker in content:
    start_idx = content.find(old_cols_marker)
    # Localizar o final do rename
    end_marker = '})'
    end_idx = content.find(end_marker, start_idx) + 2
    if start_idx != -1 and end_idx != -1:
        content = content[:start_idx] + new_cols_block + content[end_idx:]
        print("Bloco de Colunas Restaurado.")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
"""

print('=== REAPLICANDO CORREÇÕES NO VPS ===')
client.exec_command("cat << 'EOF' > /tmp/apply_fix_v2.py\n" + update_script + "\nEOF")
print(run("/var/www/hemn_cloud/venv/bin/python3 /tmp/apply_fix_v2.py"))

print('\n=== REINICIANDO SERVIÇO ===')
print(run("systemctl restart hemn_cloud.service"))

client.close()
