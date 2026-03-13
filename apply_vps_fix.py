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

# Script Python que será executado NO VPS para aplicar o patch via regex ou substituição de bloco
# Vamos reconstruir a query e o mapeamento de colunas de forma segura.

update_script = r"""
import sys
import re

path = '/var/www/hemn_cloud/cloud_engine.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Otimizar a Query (JOIN robusto e Ordem Correta)
old_query_block = r'''            q = f"""
                SELECT e.razao_social as NOME_DA_EMPRESA, 
                       concat(estab.cnpj_basico, estab.cnpj_ordem, estab.cnpj_dv) as CNPJ, 
                       estab.situacao_cadastral as SITUACAO_CADASTRAL,
                       estab.cnae_fiscal as CNAE, 
                       estab.logradouro as LOGRADOURO,
                       estab.numero as NUMERO_DA_FAIXADA,
                       estab.bairro as BAIRRO,
                       estab.CIDADE, estab.uf as UF, estab.cep as CEP, 
                       estab.ddd1, estab.telefone1, estab.ddd2, estab.telefone2 
                FROM (
                    SELECT estab.*, m.descricao as CIDADE 
                    FROM hemn.estabelecimento estab 
                    LEFT JOIN hemn.municipio m ON estab.municipio = m.codigo 
                    WHERE {where_clause} 
                    LIMIT 20000000
                ) as estab 
                JOIN hemn.empresas e ON estab.cnpj_basico = e.cnpj_basico 
            \"\"\"'''

new_query_block = r'''            # Query Otimizada para VPS: Tabela menor (subquery) deve ficar à direita para JOIN de memória
            # Adicionado SETTINGS para algoritmos de JOIN mais robustos
            q = f"""
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
            \"\"\"'''

# 2. Corrigir Mapeamento de Colunas (Encoding Seguro)
old_columns_block = r'''            final_columns = [
                'CNPJ', 'NOME DA EMPRESA', 'SITUAÇÃO CADASTRAL', 'CNAE', 
                'LOGRADOURO', 'NUMERO DA FAIXADA', 'BAIRRO', 'CIDADE', 
                'UF', 'CEP', 'TELEFONE SOLICITADO', 'OPERADORA DO TELEFONE'
            ]
            
            df = df.rename(columns={
                'NOME_DA_EMPRESA': 'NOME DA EMPRESA',
                'SITUACAO_CADASTRAL': 'SITUAÇÃO CADASTRAL',
                'NUMERO_DA_FAIXADA': 'NUMERO DA FAIXADA'
            })'''

new_columns_block = r'''            # Mapeamento com Normalização para evitar quebras de encoding Linux/Excel
            final_columns = [
                'CNPJ', 'NOME DA EMPRESA', 'SITUAÇÃO CADASTRAL', 'CNAE', 
                'LOGRADOURO', 'NUMERO DA FAIXADA', 'BAIRRO', 'CIDADE', 
                'UF', 'CEP', 'TELEFONE SOLICITADO', 'OPERADORA DO TELEFONE'
            ]
            
            # Garantir que as colunas existam no DF do Clickhouse antes do rename
            df = df.rename(columns={
                'NOME_DA_EMPRESA': 'NOME DA EMPRESA',
                'SITUACAO_CADASTRAL': 'SITUAÇÃO CADASTRAL',
                'NUMERO_DA_FAIXADA': 'NUMERO DA FAIXADA',
                'CIDADE': 'CIDADE'
            })
            
            # Forçar preenchimento de nulos para evitar 'nan' no Excel
            df = df.fillna("")'''

if old_query_block in content:
    content = content.replace(old_query_block, new_query_block)
    print("Query atualizada.")
else:
    print("Aviso: Bloco de query não encontrado exatamente. Tentando versão com escape de aspas...")
    # Tentar match mais flexível se necessário

if old_columns_block in content:
    content = content.replace(old_columns_block, new_columns_block)
    print("Colunas atualizadas.")
else:
    print("Aviso: Bloco de colunas não encontrado.")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
"""

print('=== APLICANDO CORREÇÕES NO VPS ===')
# Escapar aspas simples para o shell
client.exec_command("cat << 'EOF' > /tmp/apply_extraction_fix.py\n" + update_script + "\nEOF")
print(run("/var/www/hemn_cloud/venv/bin/python3 /tmp/apply_extraction_fix.py"))

# Reiniciar o serviço para aplicar as mudanças
print('\n=== REINICIANDO SERVIÇO ===')
print(run("systemctl restart hemn_cloud.service"))

client.close()
