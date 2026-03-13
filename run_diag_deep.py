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

def get_full(ddd, tel):
    ddd = str(ddd).replace('.0', '').strip()
    tel = str(tel).replace('.0', '').strip()
    if not tel: return ""
    return f"55{ddd}{tel}"

def select_phone(row):
    t1 = row.get('full_t1', '')
    t2 = row.get('full_t2', '')
    if t1: return t1
    return t2

try:
    client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='')
    
    # Filtros simulados (MEI, CE, ATIVA)
    where_clause = "estab.uf = 'CE' AND estab.situacao_cadastral = '02'"
    
    # Query igualzinha à original
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
            LIMIT 10
        ) as estab ON e.cnpj_basico = estab.cnpj_basico
        SETTINGS join_algorithm = 'auto'
    '''
    
    print("--- 1. RESULTADO QUERY ---")
    res = client.query(q)
    df = pd.DataFrame(res.result_rows, columns=res.column_names)
    print(f"Colunas: {df.columns.tolist()}")
    print(df.head(1).to_string())

    print("\n--- 2. PROCESSAMENTO DE TELEFONES ---")
    df['full_t1'] = df.apply(lambda x: get_full(x['ddd1'], x['telefone1']), axis=1)
    df['full_t2'] = df.apply(lambda x: get_full(x['ddd2'], x['telefone2']), axis=1)
    df['TELEFONE SOLICITADO'] = df.apply(select_phone, axis=1)
    print(df[['CNPJ', 'TELEFONE SOLICITADO']].head(1).to_string())

    print("\n--- 3. MAPEAMENTO SITUAÇÃO ---")
    sit_map = {'01':'NULA','02':'ATIVA','03':'SUSPENSA','04':'INAPTA','08':'BAIXADA'}
    df['SITUACAO_CADASTRAL'] = df['SITUACAO_CADASTRAL'].astype(str).str.zfill(2).map(sit_map).fillna(df['SITUACAO_CADASTRAL'])
    print(df[['CNPJ', 'SITUACAO_CADASTRAL']].head(1).to_string())

    print("\n--- 4. RENOMEAÇÃO E SELEÇÃO ---")
    final_columns = [
        'CNPJ', 'NOME DA EMPRESA', 'SITUAÇÃO CADASTRAL', 'CNAE', 
        'LOGRADOURO', 'NUMERO DA FAIXADA', 'BAIRRO', 'CIDADE', 
        'UF', 'CEP', 'TELEFONE SOLICITADO', 'OPERADORA DO TELEFONE'
    ]
    
    # Criamos a coluna de operadora mockada
    df['OPERADORA DO TELEFONE'] = "VIVO"
    
    df = df.rename(columns={
        'NOME_DA_EMPRESA': 'NOME DA EMPRESA',
        'SITUACAO_CADASTRAL': 'SITUAÇÃO CADASTRAL',
        'NUMERO_DA_FAIXADA': 'NUMERO DA FAIXADA'
    })
    
    df = df.fillna("")
    
    print(f"Colunas após rename: {df.columns.tolist()}")
    
    for c in final_columns:
        if c not in df.columns: 
            print(f"AVISO: Coluna '{c}' não encontrada, preenchendo com vázio.")
            df[c] = ""
    
    df_final = df[final_columns]
    print("\n--- 5. DATAFRAME FINAL ANTES DO EXCEL ---")
    print(df_final.head(3).to_string())

except Exception as e:
    print(f"Erro no diagnóstico: {e}")
    import traceback
    traceback.print_exc()
"""

# Corrigi a variável key_filename para key_path no connect
client.connect(host, port=port, username=user, key_filename=key_path)

print('=== EXECUTANDO DIAGNÓSTICO PROFUNDO NO VPS ===')
client.exec_command("cat << 'EOF' > /tmp/diag_deep_blank.py\n" + diag_script + "\nEOF")
stdin, stdout, stderr = client.exec_command("/var/www/hemn_cloud/venv/bin/python3 /tmp/diag_deep_blank.py")
print(stdout.read().decode('utf-8', errors='replace'))
print(stderr.read().decode('utf-8', errors='replace'))

client.close()
