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
import pandas as pd
from cloud_engine import CloudEngine

engine = CloudEngine()

try:
    print("--- SIMULATING CLEAN & SAFE EXTRACTION ---")
    
    q = '''
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
            estab.cep AS CEP
        FROM hemn.empresas e
        INNER JOIN (
            SELECT estab_inner.*, m.descricao as CIDADE 
            FROM hemn.estabelecimento estab_inner 
            LEFT JOIN hemn.municipio m ON estab_inner.municipio = m.codigo 
            WHERE uf = 'CE' AND situacao_cadastral = '02'
            LIMIT 5
        ) AS estab ON e.cnpj_basico = estab.cnpj_basico
        WHERE natureza_juridica != '2135'
    '''
    
    res = engine.ch_client.query(q)
    df = pd.DataFrame(res.result_rows, columns=res.column_names)
    
    # 1. Normalização Clean
    df.columns = [str(c).upper().replace('_', ' ').strip() for c in df.columns]
    
    # 2. Rename Clean (No accents)
    final_mapping = {
        'SITUACAO CADASTRAL': 'SITUACAO CADASTRAL',
        'NUMERO DA FAIXADA': 'NUMERO DA FAIXADA'
    }
    df = df.rename(columns=final_mapping)
    
    final_columns = ['CNPJ', 'NOME DA EMPRESA', 'SITUACAO CADASTRAL', 'CNAE', 'LOGRADOURO', 'NUMERO DA FAIXADA', 'BAIRRO', 'CIDADE', 'UF', 'CEP']
    
    # Check
    print(f"COLUMNS IN DF: {df.columns.tolist()}")
    for c in final_columns:
        if c in df.columns:
            print(f"Column '{c}': FOUND (Sample: '{df[c].iloc[0]}')")
        else:
            print(f"Column '{c}': NOT FOUND!")

except Exception as e:
    print(f"ERROR: {e}")
"""

print('=== EXECUTANDO DIAGNÓSTICO PROFUNDO (V3 - CLEAN) NA VPS ===')
client.exec_command("cat << 'EOF' > /tmp/deep_diag_clean.py\n" + diag_script + "\nEOF")
stdin, stdout, stderr = client.exec_command("/var/www/hemn_cloud/venv/bin/python3 /tmp/deep_diag_clean.py")
print(stdout.read().decode('utf-8', errors='replace'))
print(stderr.read().decode('utf-8', errors='replace'))

client.close()
