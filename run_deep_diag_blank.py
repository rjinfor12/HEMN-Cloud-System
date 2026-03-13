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
sys.path.append('/var/www/hemn_cloud')
from cloud_engine_vps import CloudEngine
import pandas as pd

# Mocking task updates to avoid DB dependencies if possible, or just use a real ID
engine = CloudEngine()

filters = {
    "uf": "CE",
    "situacao": "02",
    "perfil": "NAO MEI",
    "tipo_tel": "CELULAR",
    "operadora_inc": "CLARO"
}

# We want to see the state after query and after mapping
try:
    print("--- SIMULATING EXTRACTION LOGIC ---")
    
    # 1. Query Execution
    estab_conds = ["estab_inner.uf = 'CE'", "estab_inner.situacao_cadastral = '02'"]
    empresas_conds = ["natureza_juridica != '2135'"]
    params = {}
    
    estab_where = " AND ".join(estab_conds)
    empresas_where = " AND ".join(empresas_conds)
    
    q = f'''
        SELECT 
            e.razao_social AS NOME_DA_EMPRESA, 
            CONCAT(estab.cnpj_basico, estab.cnpj_ordem, estab.cnpj_dv) AS CNPJ, 
            estab.situacao_cadastral AS SITUACAO_CADASTRAL,
            estab.cnae_fiscal AS CNAE, 
            estab.logradouro AS LOGRADOURO,
            estab.numero AS NUMERO_DA_FAIXADA,
            estab.bairro AS BAIRRO,
            estab.CIDADE AS CIDADE, 
            estab.uf AS UF, 
            estab.cep AS CEP, 
            estab.ddd1 AS ddd1, 
            estab.telefone1 AS telefone1, 
            estab.ddd2 AS ddd2, 
            estab.telefone2 AS telefone2
        FROM hemn.empresas e
        INNER JOIN (
            SELECT estab_inner.*, m.descricao as CIDADE 
            FROM hemn.estabelecimento estab_inner 
            LEFT JOIN hemn.municipio m ON estab_inner.municipio = m.codigo 
            WHERE {estab_where} 
            LIMIT 10
        ) AS estab ON e.cnpj_basico = estab.cnpj_basico
        WHERE {empresas_where}
        SETTINGS join_algorithm = 'auto'
    '''
    
    res = engine.ch_client.query(q, params)
    df = pd.DataFrame(res.result_rows, columns=res.column_names)
    
    print(f"DF SHAPE: {df.shape}")
    print(f"COLUMNS RETURNED: {df.columns.tolist()}")
    print("FIRST ROW DATA (RAW):")
    print(df.iloc[0].to_dict())
    
    # 2. Reproduction of mapping logic
    df.columns = [str(c).upper().replace('_', ' ') for c in df.columns]
    print(f"COLUMNS AFTER NORMALIZATION: {df.columns.tolist()}")
    
    final_mapping = {
        'NOME DA EMPRESA': 'NOME DA EMPRESA',
        'SITUACAO CADASTRAL': 'SITUAÇÃO CADASTRAL',
        'NUMERO DA FAIXADA': 'NUMERO DA FAIXADA',
        'TELEFONE SOLICITADO': 'TELEFONE SOLICITADO',
        'OPERADORA DO TELEFONE': 'OPERADORA DO TELEFONE'
    }
    df = df.rename(columns=final_mapping)
    print(f"COLUMNS AFTER RENAME: {df.columns.tolist()}")
    
    final_columns = ['CNPJ', 'NOME DA EMPRESA', 'SITUAÇÃO CADASTRAL', 'CNAE', 'LOGRADOURO', 'NUMERO DA FAIXADA', 'BAIRRO', 'CIDADE', 'UF', 'CEP', 'TELEFONE SOLICITADO', 'OPERADORA DO TELEFONE']
    
    print("CHECKING IF FINAL COLUMNS EXIST:")
    for c in final_columns:
        exists = c in df.columns
        print(f"Column '{c}': {'YES' if exists else 'NO'}")
        if not exists:
            df[c] = ""
            
    df = df[final_columns]
    print("FINAL DF HEAD (selected columns):")
    print(df.head(1).to_string())

except Exception as e:
    print(f"ERROR: {e}")
"""

print('=== EXECUTANDO DIAGNÓSTICO PROFUNDO NA VPS ===')
client.exec_command("cat << 'EOF' > /tmp/deep_diag_blank.py\n" + diag_script + "\nEOF")
stdin, stdout, stderr = client.exec_command("/var/www/hemn_cloud/venv/bin/python3 /tmp/deep_diag_blank.py")
print(stdout.read().decode('utf-8', errors='replace'))
print(stderr.read().decode('utf-8', errors='replace'))

client.close()
