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
    # ESTRUTURA IGUAL AO NOVO CODIGO
    estab_where = "estab.uf = 'CE' AND estab.situacao_cadastral = '02'"
    empresas_where = "natureza_juridica = '2135'"
    
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
        FROM (
            SELECT estab.*, m.descricao as CIDADE 
            FROM hemn.estabelecimento estab 
            LEFT JOIN hemn.municipio m ON estab.municipio = m.codigo 
            WHERE {estab_where} 
            LIMIT 5
        ) as estab
        JOIN hemn.empresas e ON e.cnpj_basico = estab.cnpj_basico
        WHERE {empresas_where}
        SETTINGS join_algorithm = 'auto'
    '''
    
    print("--- 1. RESULTADO QUERY REESTRUTURADA ---")
    res = client.query(q)
    df = pd.DataFrame(res.result_rows, columns=res.column_names)
    print(f"Colunas Iniciais: {df.columns.tolist()}")
    print("Dados Amostra:\n", df.head(2).to_dict('records'))

    print("\n--- 2. LÓGICA DE NORMALIZAÇÃO FINAL ---")
    # Simula exatamente o que fiz no cloud_engine_vps.py
    df.columns = [c.upper().replace('_', ' ') if ' ' not in c else c.upper() for c in df.columns]
    print(f"Colunas após Normalização: {df.columns.tolist()}")
    
    final_mapping = {
        'SITUACAO CADASTRAL': 'SITUAÇÃO CADASTRAL',
        'NUMERO DA FAIXADA': 'NUMERO DA FAIXADA'
    }
    df = df.rename(columns=final_mapping)
    print(f"Colunas após Rename: {df.columns.tolist()}")
    
    final_columns = ['CNPJ', 'NOME DA EMPRESA', 'SITUAÇÃO CADASTRAL', 'CNAE', 'LOGRADOURO', 'NUMERO DA FAIXADA', 'BAIRRO', 'CIDADE', 'UF', 'CEP']
    df = df.fillna("")
    for c in final_columns:
        if c not in df.columns: df[c] = ""
    df = df[final_columns]
    
    print("\n--- 3. DATAFRAME PRONTO PARA EXCEL ---")
    print(df.to_string())
    
except Exception as e:
    print(f"Erro no diagnóstico: {e}")
    import traceback
    traceback.print_exc()
"""

print('=== EXECUTANDO DIAGNÓSTICO DE VERIFICAÇÃO FINAL NO VPS ===')
client.exec_command("cat << 'EOF' > /tmp/diag_final.py\n" + diag_script + "\nEOF")
stdin, stdout, stderr = client.exec_command("/var/www/hemn_cloud/venv/bin/python3 /tmp/diag_final.py")
print(stdout.read().decode('utf-8', errors='replace'))
print(stderr.read().decode('utf-8', errors='replace'))

client.close()
