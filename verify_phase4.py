import paramiko, os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

diag_script = r"""
import sys
import os
import pandas as pd
sys.path.append('/var/www/hemn_cloud')
from cloud_engine import CloudEngine

engine = CloudEngine()

# Simular uma extração exatamente como o código faz
tid = "VERIFY_F4"
filters = {"uf": "CE", "natureza": "2135"} # Filtros básicos (Empresários no CE)
output_dir = "/var/www/hemn_cloud/storage/results"
output_file = os.path.join(output_dir, f"Verify_F4.xlsx")

print("--- INICIANDO SIMULAÇÃO DE EXTRAÇÃO FASE 4 ---")
try:
    # Capturar loggers e progressos seria complexo aqui, vamos rodar apenas a lógica central
    # de query e DataFrame
    estab_conds = ["estab_inner.uf = 'CE'"]
    empresas_conds = ["e.natureza_juridica = '2135'"]
    estab_where = " AND ".join(estab_conds)
    empresas_where = " AND ".join(empresas_conds)
    
    q = f'''
        SELECT 
            e.razao_social AS NOME, 
            CONCAT(estab.cnpj_basico, estab.cnpj_ordem, estab.cnpj_dv) AS CNPJ, 
            estab.situacao_cadastral AS SITUACAO,
            estab.cnae_fiscal AS CNAE, 
            estab.logradouro AS RUA,
            estab.numero AS NUMERO,
            estab.bairro AS BAIRRO,
            estab.CIDADE AS CIDADE, 
            estab.uf AS UF, 
            estab.cep AS CEP, 
            estab.ddd1 AS DDD1, 
            estab.telefone1 AS TEL1, 
            estab.ddd2 AS DDD2, 
            estab.telefone2 AS TEL2
        FROM hemn.empresas e
        INNER JOIN (
            SELECT estab_inner.*, m.descricao as CIDADE 
            FROM hemn.estabelecimento estab_inner 
            LEFT JOIN hemn.municipio m ON estab_inner.municipio = m.codigo 
            WHERE {estab_where} 
            LIMIT 100
        ) AS estab ON e.cnpj_basico = estab.cnpj_basico
        WHERE {empresas_where}
    '''
    
    print("Executando query via query_df()...")
    df = engine.ch_client.query_df(q)
    
    print(f"DataFrame criado! Linhas: {len(df)}")
    print(f"Colunas originais: {df.columns.tolist()}")
    
    # Aplicar o mapeamento final
    final_mapping = {
        'NOME': 'NOME DA EMPRESA',
        'SITUACAO': 'SITUACAO CADASTRAL',
        'RUA': 'LOGRADOURO',
        'NUMERO': 'NUMERO DA FAIXADA'
    }
    df = df.rename(columns=final_mapping)
    
    for c in ['CNPJ', 'NOME DA EMPRESA', 'SITUACAO CADASTRAL', 'CNAE', 'LOGRADOURO', 'NUMERO DA FAIXADA', 'BAIRRO', 'CIDADE', 'UF', 'CEP']:
        if c not in df.columns: df[c] = ""
        else: df[c] = df[c].astype(str).replace(['nan', 'NaN', 'None', 'None', '<NA>'], "")

    print("PRIMEIRA LINHA PROCESSADA:")
    print(df.iloc[0].to_dict())
    
    # Criar arquivo debug CSV
    debug_path = "/tmp/verify_f4_debug.csv"
    df.to_csv(debug_path, index=False)
    print(f"Debug CSV criado em: {debug_path}")
    
except Exception as e:
    print(f"ERRO NA SIMULAÇÃO: {e}")
"""

print('=== RODANDO TESTE DE VERIFICAÇÃO FASE 4 NA VPS ===')
client.exec_command("cat << 'EOF' > /tmp/verify_phase4.py\n" + diag_script + "\nEOF")
stdin, stdout, stderr = client.exec_command("/var/www/hemn_cloud/venv/bin/python3 /tmp/verify_phase4.py")
print(stdout.read().decode('utf-8', errors='replace'))
print(stderr.read().decode('utf-8', errors='replace'))

client.close()
