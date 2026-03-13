import paramiko, os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

diag_script = r"""
import pandas as pd
import clickhouse_connect
import re

try:
    client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='')
    
    # Filtros simulados (MEI, CE, ATIVA)
    where_clause = "estab.uf = 'CE' AND estab.situacao_cadastral = '02' AND e.natureza_juridica = '2135'"
    
    q = f'''
        SELECT e.razao_social as NOME_DA_EMPRESA, 
               concat(estab.cnpj_basico, estab.cnpj_ordem, estab.cnpj_dv) as CNPJ, 
               estab.situacao_cadastral as SITUACAO_CADASTRAL,
               estab.cnae_fiscal as CNAE, 
               estab.logradouro as LOGRADOURO,
               estab.numero as NUMERO_DA_FAIXADA,
               estab.bairro as BAIRRO,
               estab.CIDADE, estab.uf as UF, estab.cep as CEP, 
               estab.ddd1, estab.telefone1, estab.ddd2, estab.telefone2 
        FROM hemn.empresas e
        JOIN (
            SELECT estab.*, m.descricao as CIDADE 
            FROM hemn.estabelecimento estab 
            LEFT JOIN hemn.municipio m ON estab.municipio = m.codigo 
            WHERE {where_clause} 
            LIMIT 5
        ) as estab ON e.cnpj_basico = estab.cnpj_basico
        SETTINGS join_algorithm = 'auto'
    '''
    
    print("--- 1. RESULTADO BRUTO CLICKHOUSE ---")
    res = client.query(q)
    df = pd.DataFrame(res.result_rows, columns=res.column_names)
    print(f"Colunas Iniciais: {df.columns.tolist()}")
    print("Primeira linha:\n", df.head(1).to_dict('records'))

    print("\n--- 2. NORMALIZAÇÃO DE COLUNAS (UPPER) ---")
    df.columns = [c.upper() for c in df.columns]
    print(f"Colunas após UPPER: {df.columns.tolist()}")

    print("\n--- 3. RENOMEAÇÃO (MAPPING) ---")
    mapping = {
        'NOME_DA_EMPRESA': 'NOME DA EMPRESA',
        'NOME_FANTASIA': 'NOME FANTASIA',
        'SITUACAO_CADASTRAL': 'SITUAÇÃO CADASTRAL',
        'NUMERO_DA_FAIXADA': 'NUMERO DA FAIXADA',
        'TELEFONE_SOLICITADO': 'TELEFONE SOLICITADO',
        'OPERADORA_DO_TELEFONE': 'OPERADORA DO TELEFONE'
    }
    df = df.rename(columns=mapping)
    print(f"Colunas após RENAME: {df.columns.tolist()}")
    
    print("\n--- 4. SELEÇÃO FINAL_COLUMNS ---")
    final_columns = [
        'CNPJ', 'NOME DA EMPRESA', 'SITUAÇÃO CADASTRAL', 'CNAE', 
        'LOGRADOURO', 'NUMERO DA FAIXADA', 'BAIRRO', 'CIDADE', 
        'UF', 'CEP', 'TELEFONE SOLICITADO', 'OPERADORA DO TELEFONE'
    ]
    
    for c in final_columns:
        if c not in df.columns:
            print(f"ERRO: Coluna '{c}' DESAPARECEU/NUNCA EXISTIU!")
            df[c] = "VAZIO_POR_ERRO"
            
    df_final = df[final_columns]
    print(f"Colunas Finais: {df_final.columns.tolist()}")
    print("Amostra Final:\n", df_final.head(1).to_dict('records'))

    if df_final['NOME DA EMPRESA'].iloc[0] == "":
        print("\nALERTA: 'NOME DA EMPRESA' vázio detectado!")
    
except Exception as e:
    print(f"Erro no diagnóstico: {e}")
"""

print('=== EXECUTANDO DIAGNÓSTICO DE PRECISÃO NO VPS ===')
client.exec_command("cat << 'EOF' > /tmp/diag_precision.py\n" + diag_script + "\nEOF")
stdin, stdout, stderr = client.exec_command("/var/www/hemn_cloud/venv/bin/python3 /tmp/diag_precision.py")
print(stdout.read().decode('utf-8', errors='replace'))
print(stderr.read().decode('utf-8', errors='replace'))

client.close()
